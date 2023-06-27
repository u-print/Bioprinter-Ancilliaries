import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
from math import pi
import pyperclip

def well_to_coords(well, well_plate_size, start_x, start_y):
    row = ord(well[0]) - ord('A')
    col = int(well[1:]) - 1
    x = start_x - row * well_plate_size
    y = start_y - col * well_plate_size
    return (x, y)

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.grid()
        self.create_widgets()

    def create_widgets(self):
        self.lbl_syringe_id = tk.Label(self, text="Syringe ID")
        self.lbl_syringe_id.grid(row=0, column=0)
        self.syringe_var = tk.StringVar(self)
        self.syringe_var.set("250uL")
        self.opt_syringe_id = tk.OptionMenu(self, self.syringe_var, "250uL", "1000uL", "5mL")
        self.opt_syringe_id.grid(row=0, column=1)

        self.lbl_volume = tk.Label(self, text="Extruded Volume per Well (µl)")
        self.lbl_volume.grid(row=1, column=0)
        self.txt_volume = tk.Entry(self)
        self.txt_volume.grid(row=1, column=1)

        self.lbl_pause = tk.Label(self, text="Pause (s)")
        self.lbl_pause.grid(row=2, column=0)
        self.txt_pause = tk.Entry(self)
        self.txt_pause.grid(row=2, column=1)

        self.lbl_start_well = tk.Label(self, text="Start Well")
        self.lbl_start_well.grid(row=3, column=0)
        self.txt_start_well = tk.Entry(self)
        self.txt_start_well.grid(row=3, column=1)

        self.lbl_end_well = tk.Label(self, text="End Well")
        self.lbl_end_well.grid(row=4, column=0)
        self.txt_end_well = tk.Entry(self)
        self.txt_end_well.grid(row=4, column=1)

        self.lbl_wells_per_row = tk.Label(self, text="Wells per Row")
        self.lbl_wells_per_row.grid(row=5, column=0)
        self.txt_wells_per_row = tk.Entry(self)
        self.txt_wells_per_row.grid(row=5, column=1)

        self.lbl_z_movement = tk.Label(self, text="Z Movement (mm)")
        self.lbl_z_movement.grid(row=6, column=0)
        self.txt_z_movement = tk.Entry(self)
        self.txt_z_movement.insert(0, "12")
        self.txt_z_movement.grid(row=6, column=1)

        self.lbl_plate_size = tk.Label(self, text="Centre to centre well (mm)")
        self.lbl_plate_size.grid(row=7, column=0)
        self.txt_plate_size = tk.Entry(self)
        self.txt_plate_size.insert(0, "4.5")
        self.txt_plate_size.grid(row=7, column=1)

        self.lbl_start_x = tk.Label(self, text="Start Coordinate X")
        self.lbl_start_x.grid(row=8, column=0)
        self.txt_start_x = tk.Entry(self)
        self.txt_start_x.insert(0, "293.1")
        self.txt_start_x.grid(row=8, column=1)

        self.lbl_start_y = tk.Label(self, text="Start Coordinate Y")
        self.lbl_start_y.grid(row=9, column=0)
        self.txt_start_y = tk.Entry(self)
        self.txt_start_y.insert(0, "139.4")
        self.txt_start_y.grid(row=9, column=1)

        self.btn_generate = tk.Button(self)
        self.btn_generate["text"] = "Generate GCode"
        self.btn_generate["command"] = self.generate_gcode
        self.btn_generate.grid(row=10, column=0, columnspan=2)

        self.btn_copy = tk.Button(self)
        self.btn_copy["text"] = "Copy to Clipboard"
        self.btn_copy["command"] = self.copy_to_clipboard
        self.btn_copy.grid(row=11, column=0, columnspan=2)

        self.btn_save = tk.Button(self)
        self.btn_save["text"] = "Save as GCODE"
        self.btn_save["command"] = self.save_as_gcode
        self.btn_save.grid(row=12, column=0, columnspan=2)

        self.txt_gcode = tk.Text(self)
        self.txt_gcode.grid(row=13, column=0, columnspan=2)

    def generate_gcode(self):
        try:
            # Calculate E value
            syringe_id = self.syringe_var.get()
            if syringe_id == "250uL":
                syringe_diameter = 2.3  # Corrected diameter for 250uL
            elif syringe_id == "1000uL":
                syringe_diameter = 4.61
            else:  # 5mL
                syringe_diameter = 11.73
            
            volume = float(self.txt_volume.get())  # µl
            pause = int(float(self.txt_pause.get()) * 1000)  # ms
            
            e_value = volume / (pi * (syringe_diameter / 2) ** 2)
            well_plate_size = float(self.txt_plate_size.get())
            start_x = float(self.txt_start_x.get())
            start_y = float(self.txt_start_y.get())
            
            # Get wells
            start_well = self.txt_start_well.get().upper()
            end_well = self.txt_end_well.get().upper()
    
            # Get number of wells per row
            wells_per_row = int(self.txt_wells_per_row.get())
    
            # Get Z Movement
            z_movement = self.txt_z_movement.get()
    
            # Generate gcode
            gcode = []
            current_row = start_well[0]
            current_col = int(start_well[1:])
    
            direction = 1  # forward
    
            while current_row <= end_well[0]:
                for _ in range(wells_per_row):
                    current_well = current_row + str(current_col)
                    x, y = well_to_coords(current_well, well_plate_size, start_x, start_y)
                    gcode.append(f"G1 X{x} Y{y} F1000")  # Move to the well
                    gcode.append(f"G1 Z-{z_movement} F1000")  # Move down
                    gcode.append(f"G92 E0")  # Set current extruder position to 0
                    gcode.append(f"G1 E{e_value} F100")  # Extrude
                    gcode.append(f"G4 P{pause}")  # Pause
                    gcode.append(f"G1 Z{z_movement} F1000")  # Move up
    
                    if current_well == end_well:
                        break
    
                    # Only change column if we are not at the end of the row
                    if _ != wells_per_row - 1:
                        current_col += direction
    
                if current_well == end_well:
                    break
    
                current_row = chr(ord(current_row) + 1)  # Move to the next row
    
                direction *= -1  # Change direction
    
            # Show gcode
            self.txt_gcode.delete(1.0, tk.END)
            self.txt_gcode.insert(tk.END, "\n".join(gcode))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def copy_to_clipboard(self):
        pyperclip.copy(self.txt_gcode.get(1.0, tk.END))

    def save_as_gcode(self):
        filename = filedialog.asksaveasfilename(defaultextension=".gcode")
        with open(filename, 'w') as f:
            f.write(self.txt_gcode.get(1.0, tk.END))

root = tk.Tk()
app = Application(master=root)
app.mainloop()
