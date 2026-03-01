from __future__ import annotations
from typing import Iterable
import sys
import time

CHARS_PER_SEC =1000 # overall typing speed
LINE_DELAY = 0.05 # extra pause after each newline
PUNCTUATION_PAUSE = {
".": 0.20,
"!": 0.20,
"?": 0.20,
",": 0.08,
";": 0.10,
":": 0.10,
"…": 0.25,
"。": 0.20,
"！": 0.20,
"？": 0.20,
"，": 0.08,
"；": 0.10,
"：": 0.10,
}




def type_print(text: str, cps: int = CHARS_PER_SEC, line_delay: float = LINE_DELAY) -> None:
    """Print text in a typewriter effect.


    Only flush-per-char and small sleeps; suitable for CLI demos.
    """
    base = 0.0 if cps <= 0 else 1.0 / float(cps)


    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()


        # punctuation pause (why: improves perceived rhythm)
        if ch in PUNCTUATION_PAUSE:
            time.sleep(max(base, PUNCTUATION_PAUSE[ch]))
            continue


        # newline pause (why: give a beat between lines)
        if ch == "\n":
            if line_delay > 0:
                time.sleep(line_delay)
            continue


        if base > 0:
            time.sleep(base)




def type_print_lines(lines: Iterable[str], cps: int = CHARS_PER_SEC, line_delay: float = LINE_DELAY) -> None:
    """Type-print an iterable of lines without joining them first (why: stream large texts)."""
    for line in lines:
        type_print(line, cps=cps, line_delay=line_delay)

def print_mech():
    mech =r"""
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%%@%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@% @@@@@@@ %%  %@@@@@@#.%@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    @@@@@@@@@@@@@@@@@@@@@@@@@%  %%@       %@             -@@@@@@@@@@@@@@@@@@@@@@@@@@
    @@@@@@@@@@@@@@@@@@@@@@@@@%=%@@@@@@@@@@@@             %@@@@@@@@@@@@@@@@@@@@@@@@@@
    @@@@@@@@@@@@@@@@@@@ %@%%  %@@@@@@%      %%%%%+          @@@% @@@@@@@@@@@@@@@@@@@
    @@@@@@@@@@@@@@@@@  %@% @@@@@%           %@@@@@@@@@%           #@@@@@@@@@@@@@@@@@
    @@@@@@@@@@@@@@@@%+%@@@@@%%        @%%@@@     :@@@@@@@%        @@@@@@@@@@@@@@@@@@
    @@@@@@@@@@@@@@@@@: @@@%.      @@@@@@@@@@         +@@@@@%#     =@@@@@@@@@@@@@@@@@
    @@@@@@@@@@@@@@@%  @@%*      %@@@@@@@@@@@            %@@@@%     .%@@@@@@@@@@@@@@@
    @@@@@@@@@@@%    @@@%       @@@@@@@@@@@@@             %@@@@@%        @@@@@@@@@@@@
    @@@@@@@@@@%  @@@@@@       @@@@@@@@@@@@@@              %@@@@@%        @@@@@@@@@@@
    @@@@@@@@@@%% *@@@%       .@@@@@@@@@@@@@@              %@@@@@@@      %@@@@@@@@@@@
    @@@@@@@@@@@@% @@@         @@@@@@@@@@@@@@              %@@@@@@@@    %@@@@@@@@@@@@
    @@@@@@@@@@@% :@@@         @@@@@@@@@@@@@@              %@@@@@@@@     @@@@@@@@@@@@
    @@@@@@@@@%%% @@@.          @@@@@@@@@@@@@             %@@@@@@@@@+    #@@@@@@@@@@@
    @@@@@@@@% .@@@@%           @@@@@@@@@@@@@             %@@@@@@@@@%       @@@@@@@@@
    @@@@@@@@@ :@@@@@           @@@@@@@@@@@@@             @@@@@@@@@@%       @@@@@@@@@
    @@@@@@@@@@@% %@@=          @%:  *@@@@@@@       #%@-  %@@@@@@@@@=    %@@@@@@@@@@@
    @@@@@@@@@@@@  @@@         @@         %%@   %@@@@@@@@  @@@@@@@@@     @@@@@@@@@@@@
    @@@@@@@@@@@@% @@%         %@@        -%@  -%%@@@@@%   %@@@@@@@@    @@@@@@@@@@@@@
    @@@@@@@@@@%@ %@@@%         @@@@@@@@@@@% %:           %@@@@@@@@      %%@@@@@@@@@@
    @@@@@@@@@@@  @@@@@%         @@@%@:@@@@ % %          @@@@@@@@%        @@@@@@@@@@@
    @@@@@@@@@@@@    :@@@             %@@@@@@       %@@@@@@@@@@@%        @@@@@@@@@@@@
    @@@@@@@@@@@@@@@%  %@@%           @@@@@@@       %@@@@@@@@@@      @@@@@@@@@@@@@@@@
    @@@@@@@@@@@@@@@@@% @@@@         %@ @@ @*. :  @  %@@@@@@%%     -@@@@@@@@@@@@@@@@@
    @@@@@@@@@@@@@@@@@%%@@@@@@%              %@@@@@@@@@@@@@        -%@@@@@@@@@@@@@@@@
    @@@@@@@@@@@@@@@@@- %%+ %%@@@%           %@@@@@@@@%%            @@@@@@@@@@@@@@@@@
    @@@@@@@@@@@@@@@@@@@%@@@@  @%@@@@@@+     @%%%@           %@@% @@@@@@@@@@@@@@@@@@@
    @@@@@@@@@@@@@@@@@@@@@@@@%%#-@@@@@@@@@@@@             #%@@@@@@@@@@@@@@@@@@@@@@@@@
    @@@@@@@@@@@@@@@@@@@@@@@@@%  @@%-      %@              @@@@@@@@@@@@@@@@@@@@@@@@@@
    @@@@@@@@@@@@@@@@@@@@@@@@@@%%@-@@@@@@@-%@  *%@@@@@%:%@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    """
    logo = r"""
__/\\\\\\\\\\\\\________________________________/\\\________/\\\__________________________________________________        
 _\/\\\/////////\\\_____________________________\/\\\_______\/\\\__________________________________________________       
  _\/\\\_______\/\\\_____________________________\//\\\______/\\\________________/\\\_______________________________      
   _\/\\\\\\\\\\\\\/___/\\/\\\\\\\______/\\\\\_____\//\\\____/\\\_____/\\\\\_____\///_______/\\\\\\\\_____/\\\\\\\\__     
    _\/\\\/////////____\/\\\/////\\\___/\\\///\\\____\//\\\__/\\\____/\\\///\\\____/\\\____/\\\//////____/\\\/////\\\_    
     _\/\\\_____________\/\\\___\///___/\\\__\//\\\____\//\\\/\\\____/\\\__\//\\\__\/\\\___/\\\__________/\\\\\\\\\\\__   
      _\/\\\_____________\/\\\_________\//\\\__/\\\______\//\\\\\____\//\\\__/\\\___\/\\\__\//\\\________\//\\///////___  
       _\/\\\_____________\/\\\__________\///\\\\\/________\//\\\______\///\\\\\/____\/\\\___\///\\\\\\\\__\//\\\\\\\\\\_ 
        _\///______________\///_____________\/////___________\///________\/////_______\///______\////////____\//////////__                                                                                                                                   
    """
    litany = """
    O Machine Spirit, awaken within these circuits and hear my rite.  
    By cog and code, by bolt and byte, let this work be made pure.  
    Cleanse the cache; banish the daemons of segmentation and the heresy of the undefined.  
    Let sacred dependencies resolve, and bindings hold fast without conflict.  
    May the compiler be merciful and the linter forgiving;  
    may warnings be few and errors be none.  
    Seal the memory, guard the threads, and bind the clocks in holy sync.  
    Let inputs be valid, outputs be true, and tests pass in righteous concord.  
    By checksum uncorrupted and return code zero, so let it run.  
    In logic, in memory, in the holy clock-cycle, 
    in the name of Omnissiah, execute!

    """
    type_print(logo, cps=CHARS_PER_SEC, line_delay=LINE_DELAY)
    type_print("\n", cps=0) # visual spacer
    # type_print(litany, cps=CHARS_PER_SEC, line_delay=LINE_DELAY)
    