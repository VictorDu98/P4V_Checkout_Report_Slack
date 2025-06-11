import time
import model

def main(*args):
    while True:
        current_time = time.strftime("%H:%M")
        for arg in args:
            if current_time == arg:
                GFH = model.Model("GFH")
                GFH.run()

                ISN_ENV_1 = model.Model("ISN_ENV_1")
                ISN_ENV_1.run()

                ISN_ENV_2 = model.Model("ISN_ENV_2")
                ISN_ENV_2.run()

                ISN_VFX_1 = model.Model("ISN_VFX_1")
                ISN_VFX_1.run()

                ISN_VFX_2 = model.Model("ISN_VFX_2")
                ISN_VFX_2.run()
        time.sleep(60)  # Interval trigger time

main("20:45","23:45","01:45")