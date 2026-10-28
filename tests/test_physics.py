import json
import math
import unittest
from helios.physics import Simulation, WORLDS, presets

class FlightTests(unittest.TestCase):
    def advance(self,s,seconds):
        for _ in range(round(seconds/.02)):s.step(.02)

    def test_pad_holds_without_thrust(self):
        s=Simulation();self.advance(s,10)
        self.assertEqual(s.altitude,0);self.assertEqual(s.speed,0)

    def test_launch_consumes_fuel_and_gains_height(self):
        s=Simulation();s.throttle=1
        self.advance(s,30)
        self.assertGreater(s.altitude,1000)
        self.assertLess(s.fuels[0],26000)
        self.assertGreater(s.q,0)

    def test_staging_drops_first_stage_mass(self):
        s=Simulation();m=s.mass;s.separate()
        self.assertEqual(m-s.mass,30000)
        self.assertEqual(s.engine.isp,350)
        s.separate();self.assertEqual(s.stage,1)

    def test_vacuum_orbit_remains_stable(self):
        s=Simulation(WORLDS['Moon'],presets()['Orbital Probe'],True)
        initial=s.altitude
        self.advance(s,600)
        self.assertLess(abs(s.altitude-initial),100)
        apo,peri,e=s.orbital_elements()
        self.assertLess(e,.001)
        self.assertAlmostEqual((apo+peri)/2,initial,delta=10)

    def test_save_round_trip_and_continuation(self):
        s=Simulation();s.throttle=1;self.advance(s,12)
        t=Simulation.restore(json.loads(json.dumps(s.snapshot())))
        self.advance(s,10);self.advance(t,10)
        self.assertEqual(s.snapshot(),t.snapshot())

    def test_impact_is_terminal(self):
        s=Simulation();s.y+=10;s.vy=-30;s.status='Flying'
        self.advance(s,2)
        self.assertEqual(s.status,'Crashed')
        self.assertAlmostEqual(s.altitude,0)
        t=s.time;self.advance(s,2);self.assertEqual(s.time,t)

    def test_fuel_cannot_go_negative(self):
        s=Simulation();s.fuels[0]=.001;s.throttle=1;s.step(.02)
        self.assertEqual(s.fuels[0],0)

    def test_invalid_save_rejected(self):
        d=Simulation().snapshot();d['state']['x']=float('nan')
        with self.assertRaises(ValueError):Simulation.restore(d)

    def test_bad_timestep_rejected(self):
        for dt in (0,-1,.2,math.inf,math.nan):
            with self.assertRaises(ValueError):Simulation().step(dt)

    def test_escape_trajectory(self):
        s=Simulation(orbit=True);s.vx*=2
        self.assertIsNone(s.orbital_elements()[0])

    def test_airplane_and_object_presets(self):
        for name in ('Aster Spaceplane','Orbital Probe'):
            s=Simulation(vehicle=presets()[name],orbit=True)
            self.advance(s,5)
            self.assertTrue(math.isfinite(s.altitude))

if __name__=='__main__':unittest.main()
