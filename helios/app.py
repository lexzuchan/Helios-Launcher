"""Tk desktop cockpit; all simulation state lives in physics.py."""
import csv
import json
import math
from pathlib import Path
import random
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from dataclasses import asdict
from .physics import Simulation, WORLDS, presets, Vehicle, Stage, validate_vehicle

ROOT = Path(__file__).resolve().parent.parent
BG='#080f1b'
PANEL='#111e30'
TEXT='#e8eef8'
MUTED='#8fa5c0'
GOLD='#ffba60'

class App:
    def __init__(self, root):
        self.root=root
        root.title('Helios Launcher | Anavic Studios LLC')
        root.geometry('1440x900')
        root.minsize(1100,850)
        root.configure(bg=BG)
        try:
            root.iconbitmap(str(ROOT/'assets/helios.ico'))
        except tk.TclError:
            pass
        style=ttk.Style()
        style.theme_use('clam')
        style.configure('.',background=PANEL,foreground=TEXT,font=('Segoe UI',10))
        style.configure('TButton',padding=8)
        style.map('TButton',background=[('active','#29415e')])
        style.configure('TCombobox',fieldbackground=PANEL,foreground=TEXT)
        style.map('TCombobox',fieldbackground=[('readonly',PANEL)],foreground=[('readonly',TEXT)])
        self.sim=Simulation()
        self.paused=True
        self.warp=tk.StringVar(value='1')
        self.world=tk.StringVar(value='Earth')
        self.preset=tk.StringVar(value='Helios Two Stage')
        self.mode=tk.StringVar(value='Flight')
        self.auto=tk.BooleanVar(value=False)
        self.throttle=tk.DoubleVar(value=0)
        self.pitch=tk.DoubleVar(value=90)
        self.zoom=tk.DoubleVar(value=1)
        self.rows=[]
        self.trail=[]
        self.accumulator=0
        self.last_sample=-1
        self.last=time.perf_counter()
        self.log_seen=0
        self.splash()

    def splash(self):
        self.cover=tk.Frame(self.root,bg='black')
        self.cover.pack(fill='both',expand=True)
        self.splash_image=tk.PhotoImage(file=str(ROOT/'assets/anavic-space.png')).subsample(3)
        tk.Label(self.cover,image=self.splash_image,bg='black').pack(expand=True)
        tk.Label(self.cover,text='ANAVIC STUDIOS LLC  /  INITIALIZING HELIOS',fg=GOLD,bg='black',font=('Segoe UI',12)).pack(pady=25)
        self.root.after(1400,self.build)

    def build(self):
        self.cover.destroy()
        header=tk.Frame(self.root,bg=BG)
        header.pack(fill='x',padx=18,pady=10)
        self.logo=tk.PhotoImage(file=str(ROOT/'assets/helios-launcher.png')).subsample(12)
        tk.Label(header,image=self.logo,bg=BG).pack(side='left')
        tk.Label(header,text='HELIOS LAUNCHER',bg=BG,fg=TEXT,font=('Segoe UI',23,'bold')).pack(side='left',padx=15)
        tk.Label(header,text='FLIGHT DYNAMICS LAB\nANAVIC STUDIOS LLC',bg=BG,fg=MUTED,justify='right').pack(side='right')
        body=tk.Frame(self.root,bg=BG)
        body.pack(fill='both',expand=True,padx=18)
        left=tk.Frame(body,bg=PANEL,width=240)
        left.pack(side='left',fill='y',padx=(0,12))
        left.pack_propagate(False)
        self.label(left,'MISSION SETUP',GOLD)
        self.label(left,'Environment')
        ttk.Combobox(left,textvariable=self.world,values=list(WORLDS),state='readonly').pack(fill='x',padx=12)
        self.label(left,'Vehicle')
        ttk.Combobox(left,textvariable=self.preset,values=list(presets()),state='readonly').pack(fill='x',padx=12)
        for title,fn in [('New surface flight',lambda:self.reset(False)),('New circular orbit',lambda:self.reset(True)),('Vehicle editor',self.editor),('Save mission',self.save),('Load mission',self.load),('Export telemetry CSV',self.export)]:
            ttk.Button(left,text=title,command=fn).pack(fill='x',padx=12,pady=4)
        self.label(left,'FLIGHT CONTROL',GOLD)
        ttk.Checkbutton(left,text='Gravity-turn assist',variable=self.auto).pack(anchor='w',padx=12)
        self.label(left,'Throttle (%)')
        tk.Scale(left,from_=0,to=100,variable=self.throttle,orient='horizontal',bg=PANEL,fg=TEXT,highlightthickness=0).pack(fill='x',padx=10)
        self.label(left,'Pitch (° above horizon)')
        tk.Scale(left,from_=-90,to=180,variable=self.pitch,orient='horizontal',bg=PANEL,fg=TEXT,highlightthickness=0).pack(fill='x',padx=10)
        ttk.Button(left,text='Separate stage [Space]',command=self.sim_stage).pack(fill='x',padx=12,pady=6)
        middle=tk.Frame(body,bg=BG)
        middle.pack(side='left',fill='both',expand=True)
        bar=tk.Frame(middle,bg=PANEL)
        bar.pack(fill='x')
        self.pause_button=ttk.Button(bar,text='▶ Resume [P]',command=self.toggle)
        self.pause_button.pack(side='left')
        ttk.Combobox(bar,textvariable=self.mode,values=['Flight','Orbit map'],width=12,state='readonly').pack(side='left',padx=8)
        tk.Label(bar,text='TIME ×',bg=PANEL,fg=MUTED).pack(side='left')
        ttk.Combobox(bar,textvariable=self.warp,values=['1','2','5','10','25','50'],width=5,state='readonly').pack(side='left',padx=5)
        tk.Label(bar,text='ZOOM',bg=PANEL,fg=MUTED).pack(side='left',padx=5)
        ttk.Scale(bar,from_=.2,to=5,variable=self.zoom).pack(side='left',fill='x',expand=True)
        self.canvas=tk.Canvas(middle,bg=BG,highlightthickness=0)
        self.canvas.pack(fill='both',expand=True)
        self.chart=tk.Canvas(middle,height=110,bg=PANEL,highlightthickness=0)
        self.chart.pack(fill='x',pady=(8,0))
        right=tk.Frame(body,bg=PANEL,width=238)
        right.pack(side='right',fill='y',padx=(12,0))
        right.pack_propagate(False)
        self.label(right,'LIVE TELEMETRY',GOLD)
        self.telemetry=tk.Label(right,bg=PANEL,fg=TEXT,font=('Consolas',11),justify='left',anchor='nw')
        self.telemetry.pack(fill='x',padx=12,pady=8)
        self.label(right,'MISSION EVENTS',GOLD)
        self.log=tk.Text(right,height=12,bg=BG,fg=MUTED,wrap='word',relief='flat',font=('Consolas',9))
        self.log.pack(fill='both',expand=True,padx=10,pady=8)
        tk.Label(self.root,text='P pause  •  Space stage  •  W/S throttle  •  A/D pitch  •  F flight/map  |  SI units · planar simulation',bg=BG,fg=MUTED).pack(pady=9)
        self.root.bind('<KeyPress>',self.key)
        self.root.after(16,self.tick)

    def label(self,parent,text,color=TEXT):
        tk.Label(parent,text=text,bg=PANEL,fg=color,anchor='w',font=('Segoe UI',10,'bold')).pack(fill='x',padx=12,pady=(12,6))

    def key(self,event):
        if isinstance(event.widget,(tk.Entry,tk.Text,ttk.Entry,ttk.Combobox)):
            return
        k=event.keysym.lower()
        if k=='p':self.toggle()
        elif k=='space':self.sim_stage(); return 'break'
        elif k=='w':self.throttle.set(min(100,self.throttle.get()+5))
        elif k=='s':self.throttle.set(max(0,self.throttle.get()-5))
        elif k=='a':self.pitch.set(min(180,self.pitch.get()+3))
        elif k=='d':self.pitch.set(max(-90,self.pitch.get()-3))
        elif k=='f':self.mode.set('Orbit map' if self.mode.get()=='Flight' else 'Flight')

    def toggle(self):
        self.paused=not self.paused
        self.pause_button.configure(text='▶ Resume [P]' if self.paused else 'Ⅱ Pause [P]')

    def sim_stage(self):self.sim.separate()

    def set_sim(self,sim):
        self.sim=sim
        self.paused=True
        self.accumulator=0
        self.rows=[];self.trail=[];self.last_sample=-1;self.log_seen=0
        self.log.delete('1.0','end')
        self.throttle.set(sim.throttle*100);self.pitch.set(sim.pitch);self.auto.set(sim.autopilot)
        self.world.set(sim.world.name)
        self.pause_button.configure(text='▶ Resume [P]')

    def reset(self,orbit):
        self.set_sim(Simulation(WORLDS[self.world.get()],presets()[self.preset.get()],orbit))

    def tick(self):
        now=time.perf_counter()
        elapsed=min(.1,now-self.last); self.last=now
        s=self.sim
        if not self.paused:
            s.throttle=self.throttle.get()/100
            s.pitch=self.pitch.get()
            s.autopilot=self.auto.get()
            self.accumulator+=elapsed*float(self.warp.get())
            while self.accumulator>=.02:
                s.step(.02); self.accumulator-=.02
                if s.time-self.last_sample>=.5:
                    self.last_sample=s.time
                    self.rows.append((s.time,s.altitude,s.speed,s.mass,sum(s.fuels[s.stage:]),s.q,s.pitch,s.throttle))
                    self.trail.append((s.x,s.y))
                    self.rows=self.rows[-30000:];self.trail=self.trail[-6000:]
            if s.autopilot:self.pitch.set(s.pitch);self.throttle.set(s.throttle*100)
        self.draw()
        self.root.after(33,self.tick)

    def draw(self):
        c=self.canvas;s=self.sim
        c.delete('all');w=c.winfo_width();h=c.winfo_height()
        rng=random.Random(42)
        for _ in range(90):
            x=rng.random()*w;y=rng.random()*h
            c.create_oval(x,y,x+1,y+1,fill='#5e718f',outline='')
        if self.mode.get()=='Orbit map':self.draw_map(w,h)
        else:self.draw_flight(w,h)
        c.create_text(22,25,text=f'{s.world.name.upper()}  /  {s.vehicle.name.upper()}',fill=GOLD,anchor='w',font=('Segoe UI',11,'bold'))
        c.create_text(22,50,text=f'T+ {s.time:09.1f} s    {"PAUSED" if self.paused else s.status.upper()}',fill=TEXT,anchor='w',font=('Consolas',12))
        apo,peri,e=s.orbital_elements()
        r=math.hypot(s.x,s.y);vertical=(s.x*s.vx+s.y*s.vy)/r
        fmt=lambda n:'ESCAPE' if n is None else f'{n/1000:,.1f} km'
        fuel=100*sum(s.fuels[s.stage:])/max(1,sum(st.fuel for st in s.vehicle.stages[s.stage:]))
        self.telemetry.configure(text=(f'ALTITUDE\n{s.altitude/1000:>16,.2f} km\n\nSPEED\n{s.speed:>16,.1f} m/s\n\nVERTICAL RATE\n{vertical:>16,.1f} m/s\n\nMASS / FUEL\n{s.mass:>12,.0f} kg\n{fuel:>16.1f} %\n\nDYNAMIC PRESSURE\n{s.q/1000:>16,.2f} kPa\n\nNET ACCELERATION\n{s.acceleration:>16.2f} g\n\nAPOAPSIS\n{fmt(apo):>19}\nPERIAPSIS\n{fmt(peri):>19}\n\nSTAGE {min(s.stage+1,len(s.fuels))}/{len(s.fuels)}\n{s.status}'))
        for event in s.events[self.log_seen:]:self.log.insert('end',event+'\n\n')
        self.log_seen=len(s.events);self.log.see('end')
        chart=self.chart;chart.delete('all');cw=chart.winfo_width()
        chart.create_text(12,14,text='ALTITUDE HISTORY  /  latest 5 minutes',fill=MUTED,anchor='w')
        rows=self.rows[-600:]
        if len(rows)>1:
            hi=max(1,max(row[1] for row in rows))
            pts=[]
            for i,row in enumerate(rows):pts.extend((12+i*(cw-24)/(len(rows)-1),100-70*max(0,row[1])/hi))
            chart.create_line(*pts,fill=GOLD,width=2)
            chart.create_text(cw-12,14,text=f'{hi/1000:,.1f} km',fill=TEXT,anchor='e')

    def draw_map(self,w,h):
        c=self.canvas;s=self.sim;world=s.world
        radius=max(world.radius*1.25,math.hypot(s.x,s.y)*1.15)
        scale=min(w,h)*.43/radius*self.zoom.get()
        cx,cy=w/2,h/2
        project=lambda x,y:(cx+x*scale,cy-y*scale)
        rr=world.radius*scale
        c.create_oval(cx-rr,cy-rr,cx+rr,cy+rr,fill=world.color,outline='#72a2bd',width=2)
        # Osculating conic; only display points above the surface.
        r=math.hypot(s.x,s.y);mu=world.mu
        dot=s.x*s.vx+s.y*s.vy
        ex=((s.speed**2-mu/r)*s.x-dot*s.vx)/mu
        ey=((s.speed**2-mu/r)*s.y-dot*s.vy)/mu
        e=math.hypot(ex,ey);arg=math.atan2(ey,ex)
        p=(s.x*s.vy-s.y*s.vx)**2/mu
        prev=None
        for i in range(361):
            a=i*math.pi/180;den=1+e*math.cos(a)
            if den<=0:prev=None;continue
            rr2=p/den
            if not world.radius<=rr2<=radius*8:prev=None;continue
            pt=project(rr2*math.cos(a+arg),rr2*math.sin(a+arg))
            if prev:c.create_line(*prev,*pt,fill='#46677e',dash=(4,4))
            prev=pt
        if len(self.trail)>1:
            pts=[n for x,y in self.trail for n in project(x,y)]
            c.create_line(*pts,fill=GOLD,width=2)
        x,y=project(s.x,s.y)
        c.create_oval(x-5,y-5,x+5,y+5,fill=TEXT,outline=GOLD)
        c.create_text(20,h-25,text='Dashed: osculating orbit  ·  Amber: flown trajectory',fill=MUTED,anchor='w')

    def draw_flight(self,w,h):
        c=self.canvas;s=self.sim;cx=w/2;cy=h*.48
        scale=.4*self.zoom.get()
        ground=cy+s.altitude*scale+45
        if ground<h:
            c.create_rectangle(0,ground,w,h,fill=s.world.color,outline='')
            c.create_line(0,ground,w,ground,fill='#9bb8ce')
        for yy in range(100,int(h),70):
            c.create_line(w-40,yy,w-24,yy,fill='#354a61')
        a=math.radians(s.pitch)
        def p(x,y):return cx+x*math.cos(a)-y*math.sin(a),cy-x*math.sin(a)-y*math.cos(a)
        shape=[(35,0),(-20,-10),(-30,-22),(-27,0),(-30,22),(-20,10)] if s.vehicle.kind=='plane' else [(40,0),(15,-10),(-24,-10),(-35,-20),(-28,0),(-35,20),(-24,10),(15,10)]
        if s.vehicle.kind=='object':shape=[(18,0),(0,-18),(-18,0),(0,18)]
        if s.throttle>0 and s.engine and s.fuels[s.stage]>0 and s.status not in ('Crashed','Landed'):
            flame=[p(-26,-7),p(-40-35*s.throttle,0),p(-26,7)]
            c.create_polygon(*[z for pt in flame for z in pt],fill=GOLD,outline='#ff693e')
        c.create_polygon(*[z for pt in shape for z in p(*pt)],fill=TEXT,outline=GOLD,width=2)
        c.create_oval(cx-60,cy-60,cx+60,cy+60,outline='#29435d',dash=(3,6))
        c.create_line(cx-80,cy,cx-65,cy,fill=MUTED)
        c.create_line(cx+65,cy,cx+80,cy,fill=MUTED)
        c.create_text(cx,cy+95,text=f'PITCH {s.pitch:.0f}°   /   THROTTLE {s.throttle*100:.0f}%',fill=TEXT,font=('Consolas',12))
        c.create_text(22,h-28,text='Vehicle-follow camera · local horizon · vehicle drawn at fixed size',fill=MUTED,anchor='w')
        if s.status in ('Crashed','Landed'):
            c.create_text(cx,cy-115,text=s.status.upper(),fill=GOLD,font=('Segoe UI',30,'bold'))

    def save(self):
        path=filedialog.asksaveasfilename(defaultextension='.json',filetypes=[('Mission JSON','*.json')])
        if path:
            try:Path(path).write_text(json.dumps(self.sim.snapshot(),indent=2),encoding='utf-8')
            except OSError as e:messagebox.showerror('Save failed',str(e))

    def load(self):
        path=filedialog.askopenfilename(filetypes=[('Mission JSON','*.json')])
        if path:
            try:self.set_sim(Simulation.restore(json.loads(Path(path).read_text(encoding='utf-8'))))
            except (OSError,ValueError,KeyError,TypeError,OverflowError) as e:messagebox.showerror('Invalid mission',str(e))

    def export(self):
        path=filedialog.asksaveasfilename(defaultextension='.csv',filetypes=[('CSV','*.csv')])
        if path:
            try:
                with open(path,'w',newline='',encoding='utf-8') as f:
                    writer=csv.writer(f)
                    writer.writerow(['time_s','altitude_m','speed_m_s','mass_kg','fuel_kg','dynamic_pressure_Pa','pitch_deg','throttle'])
                    writer.writerows(self.rows)
            except OSError as e:messagebox.showerror('Export failed',str(e))

    def editor(self):
        win=tk.Toplevel(self.root);win.title('Vehicle lab · JSON configuration');win.geometry('700x680');win.configure(bg=PANEL)
        tk.Label(win,text='Edit SI units. Apply starts a new paused surface mission.\nkind: rocket, plane, object · stages ordered bottom to top',bg=PANEL,fg=TEXT).pack(pady=12)
        text=tk.Text(win,bg=BG,fg=TEXT,insertbackground=TEXT,font=('Consolas',11),undo=True)
        text.pack(fill='both',expand=True,padx=15)
        text.insert('1.0',json.dumps(asdict(self.sim.vehicle),indent=2))
        def apply():
            try:
                v=json.loads(text.get('1.0','end'))
                v['stages']=[Stage(**s) for s in v['stages']]
                validate_vehicle(v)
                vehicle=Vehicle(**v)
                self.set_sim(Simulation(WORLDS[self.world.get()],vehicle))
                win.destroy()
            except (ValueError,KeyError,TypeError) as e:messagebox.showerror('Invalid vehicle',str(e),parent=win)
        ttk.Button(win,text='Apply vehicle',command=apply).pack(pady=10)

def main():
    root=tk.Tk()
    app=App(root)
    root.mainloop()
