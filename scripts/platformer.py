#!/usr/bin/env python3

import threading
import time
import math
import pygame
import json 
import subprocess 
import os

eww_bin = ["eww", "-c", f"{os.path.expanduser('~')}/.config/eww/platformer"]
board = (1920, 1020)
platforms = []
fps = 60

class Area2D: 
    def __init__(self, x, y, width, height): 
        self.x = x 
        self.y = y 
        self.width = width 
        self.height = height

    def collision(self, a): 

        if self.x + self.width < a.x or a.x +a.width < self.x:
            return False

        if self.y + self.height < a.y or a.y +a.height < self.y:
            return False

        return True

class player(Area2D): 
    def __init__(self, speed = 1, gravity=0.5, jump=18):
        super().__init__(10, 10, 50, 50)
        self.speed = speed
        self.gravity = gravity 
        self.jump = jump
        self.yvelocity = 0
        getinp = threading.Thread(target=self.getInput, daemon=True)
        getinp.start()

        # face 
        self.halign = "center"
        self.valign = "center"


    def getInput(self): 
        global fps
        run = True
        while run: 
            time.sleep(1/fps)
            for event in pygame.event.get(): 
                if event.type == pygame.QUIT: 
                    run = False
                    pygame.quit()
                    exit(0)

            keys = pygame.key.get_pressed()

            self.movement(keys)
            self.handle_gravity()


    def movement(self, keys): 
        # jumping
        if keys[pygame.K_UP]: 
            self.y += 1
            for p in platforms:
                if self.collision(p):
                    self.yvelocity = -self.jump
                    break

            self.y -= 1

        # left right
        xd = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT])

        if xd > 0: 
            self.halign = "end"
        elif xd < 0:
            self.halign = "start"
        else: 
            self.halign = "center"
    
        self.x += xd*self.speed
        if self.x <= 0 or self.x+self.width >= board[0]: 
            self.x -= xd*self.speed 

        for p in platforms:
            if self.collision(p): 
                self.x -= xd*self.speed

    def handle_gravity(self): 
        self.y += self.yvelocity 
        if self.yvelocity > 2: 
            self.valign = "end"
        elif self.yvelocity < -2:
            self.valign = "start"
        else: 
            self.valign = "center"

        c = False
        for p in platforms: 
            if self.collision(p): 
                c = True
                if self.yvelocity < 0:
                    rstep = 1
                else: 
                    rstep = -1

                while self.collision(p): 
                    self.y += rstep

                self.yvelocity = 0

        if not c: 
            self.yvelocity += self.gravity

def recurse(node, apps, output): 
    if "app_id" in node and node["app_id"]:

        node["rect"]["x"] -= output["rect"]["x"]
        node["rect"]["y"] -= output["rect"]["y"]

        if node["type"] == "floating_con": 
            apps.append({
                "rect": node["rect"],
            })

    for n in node["nodes"]: 
        recurse(n, apps, output)

    for n in node["floating_nodes"]: 
        recurse(n, apps, output)

def update_platforms():
    global platforms
    while True:
        result = subprocess.run("swaymsg -r -t get_tree", shell=True, capture_output=True, text=True).stdout
        result = json.loads(result)

        result2 = subprocess.run("swaymsg -r -t get_workspaces", shell = True, capture_output=True, text=True).stdout
        result2 = json.loads(result2)
        focus = 0

        for res in result2: 
            if res["focused"]: 
                focus = res["name"]

        apps = []
        for output in result["nodes"]:
            if output["name"] != "eDP-1": 
                continue 

            for workspace in output["nodes"]: 
                if not workspace["name"] == focus: 
                    continue

                recurse(workspace, apps, output)

        platforms.clear() 
        platforms = [Area2D(0, 1020, 1920, 60)]
        for app in apps: 
            platforms.append(Area2D(
                app["rect"]["x"], 
                app["rect"]["y"], 
                app["rect"]["width"], 
                app["rect"]["height"]))

        time.sleep(1/fps)


def main():
    p = player(speed = 7, jump=15)

    getwindows = threading.Thread(target=update_platforms, daemon=True)
    getwindows.start()

    while True: 
        data = {
            "x": p.x,
            "y": p.y,
            "width": p.width,
            "height": p.height,
            "halign": p.halign, 
            "valign": p.valign
        }
        subprocess.run(eww_bin+["update", f"player={json.dumps(data)}"])
        time.sleep(1/fps)

if __name__ == "__main__":
    pygame.init()
    window=pygame.display.set_mode((300, 300))
    pygame.display.set_caption("controller")
    main()
