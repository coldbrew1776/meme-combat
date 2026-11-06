-- FCEUX script: start the game, hold right+B, save emulator frames into tmp/.
-- gui.savescreenshotas is FCEUX's native frame capture: it writes only the
-- native NES picture, never the host desktop or the emulator chrome.
local dir = assert(os.getenv("CAPDIR"), "Set CAPDIR to an existing absolute capture directory")
assert(type(gui.savescreenshotas) == "function", "FCEUX screenshot API is unavailable")
-- Fail before playing if the capture directory is missing or unwritable.
local ready = assert(io.open(dir.."/capture-complete.txt", "w"))
ready:write("Capture in progress\n")
ready:close()
local f = 0
local shots = {[60]="title", [100]="two_players", [200]="level_banner", [330]="play1", [600]="play2", [900]="play3"}
for _, name in pairs(shots) do os.remove(dir.."/"..name..".png") end
while true do
  -- Exercise Select in both directions before starting a one-player game.
  if f == 90 or f == 105 then joypad.set(1, {select=true}) end
  if f == 120 then joypad.set(1, {start=true}) end
  if f > 125 then joypad.set(1, {right=true, B=(f%10<5), A=(f%90<10)}) end
  if shots[f] then
    local path = dir.."/"..shots[f]..".png"
    gui.savescreenshotas(path)
  end
  f = f + 1
  if f > 950 then
    -- Saving is queued until the frame completes. Check after all requested
    -- frames, rather than treating a queued capture as a missing file.
    for _, name in pairs(shots) do
      local path = dir.."/"..name..".png"
      local image = assert(io.open(path, "rb"), "Screenshot was not saved: "..path)
      assert(image:read(8) == "\137PNG\r\n\26\n", "Screenshot is not a PNG")
      image:close()
    end
    local result = assert(io.open(dir.."/capture-complete.txt", "w"))
    result:write("Captured title, player selection, level banner, and three gameplay frames.\n")
    result:close()
    os.exit(0)
  end
  emu.frameadvance()
end
