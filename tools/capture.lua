-- FCEUX script: start the game, hold right+B, save emulator frames into tmp/.
-- gui.screenshotas is FCEUX's native frame capture: it writes only the
-- 256x240 NES picture, never the host desktop or the emulator chrome.
local dir = os.getenv("CAPDIR") or "tmp"
local f = 0
local shots = {[60]="title", [200]="level_banner", [330]="play1", [600]="play2", [900]="play3"}
while true do
  if f == 120 then joypad.set(1, {start=true}) end
  if f > 125 then joypad.set(1, {right=true, B=(f%10<5), A=(f%90<10)}) end
  if shots[f] then gui.screenshotas(dir.."/"..shots[f]..".png") end
  f = f + 1
  if f > 950 then os.exit(0) end
  emu.frameadvance()
end
