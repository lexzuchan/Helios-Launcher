"""Create real widgets, render both cameras, and exercise the vehicle lab."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import tkinter as tk
from helios.app import App

root=tk.Tk()
app=App(root)
# Cancel splash timer before explicitly creating the cockpit.
for callback in root.tk.call('after','info'):
    root.after_cancel(callback)
app.build()
root.update()
app.draw()
app.mode.set('Orbit map')
app.reset(True)
app.draw()
app.editor()
root.update()
root.destroy()
print('Desktop smoke test passed: splash, cockpit, map, editor')
