import math as m

def print_time(time,msg='',ns=False):
    if ns:
        print(f"{(time):0.2f} ns -> {(time/(10**6)):0.2f} ms")
    else:
        if time/60 > 1:
            if time/3600 > 1:
                print(f"{int(time/3600)}:{int(((time/3600)-int(time/3600))*60)}:{m.ceil(((((time/3600)-int(time/3600))*60)-int(((time/3600)-int(time/3600))*60))*60)} {msg}")
            else:
                print(f"00:{int(time/60)}:{m.ceil(((time/60)-int(time/60))*60)} {msg}")
        else:
            print(f"00:00:{(time):0.2f} {msg}")
