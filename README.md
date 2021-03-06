# Protocol 0 control surface script for ableton 10

Protocol 0 is a control surface script written in python 2 (moving to python3/Live 11 as soon as tiny problems are handled).
It is a selected track control like script I wrote to automate boring tasks.
It is specifically targeted to working in session view. I did not use it yet to work in arrangement.

## Technical Foreword

This script is tailor made for my gear and workflow and is probably thus of little interest
to users. But it could be interesting to remote scripts devs !

There is a few specificities / dependencies to bear in mind if anyone would ever want to test it :
- The biggest one is on a famous remote script as I'm using a few of its classes (in particular for scheduling, using Live browser and a few others, see the code).
  I'm not gonna give the name because I'm not so sure this kind of use of the code is allowed by the EULA.
  Without this script in your remote script folder, protocol0 will fail miserably.
- External Software dependencies on python3 and autoHotkey (hard dependencies). Paths can be configured by creating and editing the .env.json file.
- Synths targeted (Prophet rev2, Serum ..). Not blocking
- Push2 handling code. Not blocking

Apart from the first point, these external dependencies should not prevent the script from loading or working in degraded state but it will prevent
the script from dispatching keys and clicks to the interface if you don't set up the .env.json file.

> The code is not stable even on master and will probably throw a lot of errors.

## Features

I started writing the script specifically because I thought recording my rev2 was tedious. Later on I realized I would
probably produce better if I was working more in session view and experiment instead of rushing to arrangement.
So now it is more of a session view tool. My goal is to be able to produce better quality music faster in session view by experimenting
fast without too much technical hassle and get over the 8 bars loop problem :p 

Specifically it aims to achieve :
- An integration with my generic FaderFox EC4 midi controller (could be used by any midi configurable controllers). Uses presses / long presses / button scrolls and shift functionality (handled by the script, not the controller). 
- A better workflow in session view
- A better workflow when using external synthesizers
- A better workflow when using automation in session view (without the need to define red automation envelopes by hand)
- A better way to show / hide vsts and change presets (specifically drums using simpler and the synths I use most : Prophet Rev2, Minitaur and Serum). Mostly leveraging program change
- A lot of little improvements in the session view including:
> - Fixed length recording
> - Memorization of the last clip played opening some possibilities in playing live or instant session state recall at startup
> - Automatic track, clip, scene naming / coloring according to set state
> - a GroupTrack template defined in the script
> - One shot clips definable by name
> - Simple Scene Follow actions definable by name
> - Automatic tracks volume mixer lowering to never go over 0db (except when a limiter is set) 
> - Integration with push2 (automatic configuration of a few display parameters depending on the type of track)

<br><br>
The bigger part of the script is dedicated to the handling of external synths and automation.

### External Synths
- The script is able to record both midi and audio at the same time doing fixed length recordings.
- It can record multiple versions of the same midi (not at the same time obviously)
- Midi and audio clips are linked (start / end / looping, suppression ..)

### Automation
> This is going to be dropped very soon. it's too complicated and not so useful.

> This is by far the most complex part of the script
> The goal is to manage chained dummy clips to play with them in session.
> 2nd goal is to handle automation via midi clip notes without using the very boring red automation curves

So : for each parameter we want to automate in a track 2 tracks are going to be created : one audio and one midi. (They will be grouped in a group track with the main track).
That's a lot of clutter on the interface but the best way to achieve what I wanted.

#### Automation audio tracks
- It handles creating dummy tracks for each mapped parameter of a track at a button click.
- We can create as many audio dummy tracks (with dummy clips obviously !) as parameters we want to map
- Audio tracks are automatically chained together and we can solo / mute effects in the chain

#### Automation midi tracks
- Each audio track is linked to a midi track
- Audio / midi clips are linked (same as the external synth tracks)
- Midi notes in the midi clips define the automation curves in the synced audio clip
- We can configure ableton like curves in the midi clips by scrolling a control.
- Midi clips should be monophonic (as notes are mapped to automation) and the code is ensuring this by automatic remapping of manual note changes (can be surprising at first ^^)

## Usage
If you want to try the script try the following :
- clone the repo in your remote scripts directory
- Ensure python3 and AutoHotkey are installed on your system (if you're on windows)
- create a .env.json file by duplicating the .env.example.json and fill in the paths
- Try using a controller with configurable note, CC and midi channels or modify the mappings in ./components/actionGroups. The bulk of the script uses the midi channel 15 and notes / CCs from 1 to 16.

## Development

I've written a technical google doc that details important parts of the script object model and techniques. 
Also a few remote scripts concepts are explained. [see this google doc](https://docs.google.com/document/d/1H5pxHiAWlyvTJJPb2GCb4fMy_26haCoi709zmcKMTYg/edit?usp=sharing)

I'm working on the dev branch and releasing to master when a stable state is reached.

### Tools

- `make test` runs the test suite (pytest) I've written a few unit tests mostly related to non LOM stuff.
- `make lint` runs the linting tools on the whole project. I'm using flake8 and mypy for type checking.
- The code is formatted with black

