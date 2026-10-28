"""Planar SI-unit flight dynamics, independent of the desktop interface."""
from dataclasses import dataclass, asdict
import math

G0 = 9.80665

@dataclass(frozen=True)
class World:
    name: str
    radius: float
    mu: float
    density: float
    scale_height: float
    color: str

WORLDS = {
    'Earth': World('Earth', 6371000, 3.986004418e14, 1.225, 8500, '#227bb1'),
    'Moon': World('Moon', 1737400, 4.9048695e12, 0, 1, '#687481'),
    'Mars': World('Mars', 3389500, 4.282837e13, .020, 11100, '#a5553b'),
}

@dataclass
class Stage:
    dry: float = 4000
    fuel: float = 26000
    thrust: float = 550000
    isp: float = 310

@dataclass
class Vehicle:
    name: str
    kind: str
    payload: float
    area: float
    cd: float
    wing: float
    stages: list

def presets():
    return {
        'Helios Two Stage': Vehicle('Helios Two Stage', 'rocket', 1400, 8, .28, 0,
                                   [Stage(4000,26000,550000,310), Stage(900,6500,110000,350)]),
        'Aster Spaceplane': Vehicle('Aster Spaceplane', 'plane', 3500, 12, .035, 50,
                                   [Stage(3500,14000,300000,900)]),
        'Orbital Probe': Vehicle('Orbital Probe', 'object', 600, 2, .3, 0, []),
    }

class Simulation:
    def __init__(self, world=None, vehicle=None, orbit=False):
        self.world = world or WORLDS['Earth']
        self.vehicle = vehicle or presets()['Helios Two Stage']
        self.stage = 0
        self.fuels = [s.fuel for s in self.vehicle.stages]
        self.x, self.y = 0., self.world.radius + (200000 if orbit else 0)
        self.vx = math.sqrt(self.world.mu/self.y) if orbit else 0.
        self.vy = 0.
        self.pitch = 90.
        self.throttle = 0.
        self.time = 0.
        self.status = 'Orbit' if orbit else 'On pad'
        self.q = self.heat = self.acceleration = 0.
        self.max_altitude = self.altitude
        self.events = ['Flight initialized']
        self.history = []
        self.autopilot = False

    @property
    def altitude(self):
        return math.hypot(self.x,self.y)-self.world.radius

    @property
    def speed(self):
        return math.hypot(self.vx,self.vy)

    @property
    def mass(self):
        return self.vehicle.payload + sum(s.dry + self.fuels[i] for i,s in enumerate(self.vehicle.stages) if i>=self.stage)

    @property
    def engine(self):
        return self.vehicle.stages[self.stage] if self.stage < len(self.vehicle.stages) else None

    def separate(self):
        if self.stage < len(self.vehicle.stages)-1:
            self.stage += 1
            self.events.append(f'T+{self.time:.1f}: stage {self.stage+1} separated')

    def orbital_elements(self):
        r = math.hypot(self.x,self.y)
        h = self.x*self.vy-self.y*self.vx
        energy = self.speed**2/2-self.world.mu/r
        e = math.sqrt(max(0,1+2*energy*h*h/self.world.mu**2))
        if energy >= 0:
            return None, h*h/self.world.mu/(1+e)-self.world.radius, e
        a = -self.world.mu/(2*energy)
        return a*(1+e)-self.world.radius, a*(1-e)-self.world.radius, e

    def step(self, dt):
        if not math.isfinite(dt) or dt <= 0 or dt > .1:
            raise ValueError('Physics step must be in (0, 0.1] seconds')
        if self.status in ('Crashed','Landed'):
            return
        r = math.hypot(self.x,self.y)
        nx,ny = self.x/r,self.y/r
        tx,ty = ny,-nx
        vr,vt = self.vx*nx+self.vy*ny, self.vx*tx+self.vy*ty
        if self.autopilot and self.vehicle.kind == 'rocket':
            self.pitch = max(0,90-max(0,self.altitude-1000)/750)
            apo,_,_ = self.orbital_elements()
            if apo is not None and apo >= 220000:
                self.throttle = 0
        engine = self.engine
        thrust = 0.
        if engine and self.fuels[self.stage]>0:
            if self.vehicle.kind != 'plane' or self.altitude < 30000:
                requested = engine.thrust*max(0,min(1,self.throttle))
                used = min(self.fuels[self.stage],requested/(engine.isp*G0)*dt)
                thrust = used*engine.isp*G0/dt
                self.fuels[self.stage] -= used
                if self.fuels[self.stage] == 0:
                    self.events.append(f'T+{self.time:.1f}: fuel depleted')
        angle = math.radians(self.pitch)
        dx,dy = tx*math.cos(angle)+nx*math.sin(angle),ty*math.cos(angle)+ny*math.sin(angle)
        rho = self.world.density*math.exp(-max(0,self.altitude)/self.world.scale_height)
        speed = self.speed
        self.q = .5*rho*speed*speed
        drag = self.q*self.vehicle.cd*self.vehicle.area
        # Plane lift uses angle of attack in the local tangent/radial frame.
        aoa = angle-math.atan2(vr,vt)
        cl = max(-1.2,min(1.2,2*math.pi*math.sin(aoa)))
        lift = self.q*self.vehicle.wing*cl
        drag += self.q*self.vehicle.wing*.06*cl*cl
        m = self.mass
        ax = -self.world.mu*nx/r**2 + thrust*dx/m
        ay = -self.world.mu*ny/r**2 + thrust*dy/m
        if speed>0:
            ax += (-drag*self.vx-lift*self.vy)/(m*speed)
            ay += (-drag*self.vy+lift*self.vx)/(m*speed)
        if self.status=='On pad' and (ax*nx+ay*ny)<=0:
            self.time += dt
            return
        self.status='Flying'
        self.vx += ax*dt
        self.vy += ay*dt
        self.x += self.vx*dt
        self.y += self.vy*dt
        self.time += dt
        self.acceleration=math.hypot(ax,ay)/G0
        self.heat=1.83e-4*math.sqrt(rho/1.0)*speed**3
        self.max_altitude=max(self.max_altitude,self.altitude)
        if self.altitude<0:
            self.status='Landed' if speed<8 else 'Crashed'
            rr=math.hypot(self.x,self.y)
            self.x*=self.world.radius/rr
            self.y*=self.world.radius/rr
            self.vx=self.vy=0
            self.throttle=0
            self.events.append(f'T+{self.time:.1f}: {self.status}')

    def snapshot(self):
        return dict(schema=1,world=self.world.name,vehicle=asdict(self.vehicle),
                    state={k:getattr(self,k) for k in ('stage','fuels','x','y','vx','vy','pitch','throttle','time','status','max_altitude','autopilot')})

    @classmethod
    def restore(cls,data):
        if data['schema']!=1:
            raise ValueError('Unsupported save version')
        v=dict(data['vehicle'])
        v['stages']=[Stage(**s) for s in v['stages']]
        validate_vehicle(v)
        sim=cls(WORLDS[data['world']],Vehicle(**v))
        state=data['state']
        for k in ('x','y','vx','vy','pitch','throttle','time','max_altitude'):
            if not isinstance(state[k],(int,float)) or not math.isfinite(state[k]):
                raise ValueError('Invalid numerical state')
        if not isinstance(state['stage'],int) or not 0<=state['stage']<=max(0,len(v['stages'])-1):
            raise ValueError('Invalid stage')
        if len(state['fuels'])!=len(v['stages']) or any(not math.isfinite(f) or not 0<=f<=s.fuel for f,s in zip(state['fuels'],v['stages'])):
            raise ValueError('Invalid fuel state')
        if state['status'] not in ('On pad','Flying','Orbit','Crashed','Landed') or math.hypot(state['x'],state['y'])<sim.world.radius*.99:
            raise ValueError('Invalid position or status')
        for k in sim.snapshot()['state']:
            setattr(sim,k,state[k])
        return sim

def validate_vehicle(v):
    if v['kind'] not in ('rocket','plane','object') or not isinstance(v['name'],str) or len(v['stages'])>10:
        raise ValueError('Invalid vehicle type or stages')
    for key in ('payload','area','cd','wing'):
        n=v[key]
        if not isinstance(n,(int,float)) or not math.isfinite(n) or not 0<=n<=1e9:
            raise ValueError('Invalid '+key)
    if v['payload']<=0:
        raise ValueError('Payload must be positive')
    for s in v['stages']:
        for key in ('dry','fuel','thrust','isp'):
            n=getattr(s,key)
            if not math.isfinite(n) or not 0<n<=1e10:
                raise ValueError('Stage values must be finite and positive')
