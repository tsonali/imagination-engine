#!/usr/bin/env python3
"""Beat 133 gold script batch — 7 gap-filling scripts for A_gold.jsonl.
Gaps: northern lights, cave diving, motorcycle canyon, whitewater kayak,
spacewalk, childhood home return, trapeze first flight.
"""

import json, os

SCRIPTS = [
    {
        "intake": "I want to watch the northern lights alone from a field in Iceland at midnight, the sky moving above me.",
        "prompt": "I want to stand alone in an Icelandic field at midnight and watch the northern lights fill the sky above me.",
        "script": """The cold is immediate and specific.

Not the cold of a city in winter, with its trapped air and exhaust and residual warmth from walls and glass — this is field cold, open-sky cold, the cold that comes when there is nothing between you and several hundred kilometers of Arctic air. Your breath comes out white. Your face knows the temperature before any other part of you does.

The field is flat and dark. The nearest structure is far enough that its light does not reach you. Underfoot, the ground is hard — frozen moss, packed earth, the specific firmness of Icelandic ground in late autumn. Your boots are good and the cold has not yet reached your feet, but you can feel it working at the seams.

The sky is clear.

This is the first thing — the clarity. The Milky Way is visible as a physical object, a band of compressed starlight running from south to north, and you can see it as depth, as distance, not just as light on a surface. The stars at the edges of your vision are as bright as the ones you look at directly. There are no clouds anywhere in the visible sky.

Then the light begins.

It does not appear suddenly. It arrives the way the first gray of dawn arrives — you are aware of it before you can be certain it is real. A faint green wash at the northern horizon, a color that is not quite right for the sky, a color that does not belong to stars or moonrise. Then the wash brightens, and the shape of it changes, and you understand that it is moving.

The aurora australis is not a flat sheet. It is a curtain in three dimensions — folds and waves moving through it, the folds independent of each other, the motion slow enough to watch develop. The green is primary at first, the green of shallow water over sand, the green of certain mosses in direct sun. It runs in a band from east to west, maybe thirty degrees above the horizon, and within that band the individual rays are visible: fine vertical lines, lighter and darker, shifting laterally.

Then the upper edge of the band brightens and turns.

The color at the top is not green. Where the green rays climb highest into the thinner atmosphere, they shift toward violet — a violet-rose that takes several minutes to recognize as a separate color from the green, a color that emerges gradually and then is unmistakably there. The upper edge of the aurora is now a different color from its lower edge, and between them is every intermediate shade.

You stop thinking about the cold.

The mechanism of attention changes when you are watching something this large move. The aurora is roughly sixty degrees of arc from edge to edge — from one horizon to another, spanning the whole northern sky, and when you look at its center the edges are in your peripheral vision, and all of it is moving. The folds ripple. A new ray brightens and fades. The western edge moves south and then withdraws.

There is no sound.

The field is absolutely quiet. No wind at this moment, no traffic, no animal sound from anywhere in this direction. The aurora makes no sound — sound would require an atmosphere dense enough to carry it, and the aurora happens eighty kilometers up, where there is almost no atmosphere. What you are watching is silent by physics. The light comes to you and that is all.

A new band forms south of the first.

This one is dimmer at first, then brightens. It runs roughly parallel to the first band, and for a moment the two bands are separate and distinct, and the dark sky between them is visible. Then the two bands connect — the folds merge, the gap between them fills — and the aurora is now a single formation spanning an even greater arc than before, top to bottom, east to west, the entire northern third of the sky occupied.

The cold returns to your awareness.

Your feet are cold now, the real cold, the cold that asks something of you. Your fingers in the gloves are cold. Your face has gone past the initial sharpness into a steady discomfort that is not yet pain. You know you will need to go inside soon.

But not yet.

The aurora is still moving. The folds still shift. The green is still green and the rose at the upper edge is still rose and the stars behind the aurora are still visible through it, through the thin plasma that is causing the light, and you are standing in a field in Iceland at midnight watching light made from the solar wind collide with the atmosphere eighty kilometers above your head, and the cold is real and your breath is white and the sky is doing this."""
    },
    {
        "intake": "I want to cave dive — swimming through an underwater passage in a cenote in Mexico, the flashlight cutting dark water, the rock ceiling close.",
        "prompt": "I want to cave dive a cenote in Mexico — the passages, the dark water, the narrow places, the way light behaves underground.",
        "script": """The water is the first temperature.

Not warm, not cold by open-water standards, but colder than your skin expects at the first contact — a freshwater temperature, the temperature of groundwater that has been underground long enough to lose all memory of the sun. Your wetsuit takes the initial shock and then equilibrates, and after thirty seconds you are comfortable, and the water is still the same temperature but you no longer notice it the same way.

The entrance is a circular opening in the limestone floor, ten meters across, the edge of it marked by a rope that runs down and into the dark.

You drop below the surface.

The transition is immediate. The sounds of the above-ground world — birds, wind in the jungle canopy, the sound of other divers on the platform — cut off the moment your ears go under. What replaces it is the sound of your own breathing apparatus: the specific sound of gas coming through the regulator, the sound of your exhalation rising in a cone of bubbles toward the ceiling. The water here, at the entrance, is still lit by the opening above you — turquoise light, diffuse, the light of sky filtered through fifteen meters of clear freshwater. The visibility is extraordinary. You can see the rope descending into the dark below you. You can see the walls of the cenote, limestone streaked with mineral deposits, the rock pitted and smooth in alternating sections.

The halocline is at six meters.

You pass through it and feel it before you see it — a layer where the freshwater meets the older saltwater that has infiltrated the cave system from the coast, two water bodies of different densities that do not mix, the boundary between them optically distorted, the way looking through two panes of glass at different angles distorts the image behind them. Your mask fogs at the halocline and then clears. Below the halocline the water is saltier and colder and your buoyancy changes — you are slightly more buoyant in the saltwater and you compensate without thinking about it, a small exhale, a slight deflation of the vest.

The passage begins at the base of the open cenote.

The rope leads into a horizontal opening in the far wall, maybe two meters wide and one and a half meters tall. The walls close in. The ceiling, which was fifteen meters above you at the entrance, is now within arm's reach. Your flashlight cuts a cone of light into the passage ahead — the walls are white limestone here, undissolved, cleaner than the entrance walls, and the light reflects back off them and off the silt on the floor, which is fine and white and settles slowly when disturbed and does not settle quickly.

You do not disturb the silt.

This is the discipline of cave diving — finning technique that keeps the fin tips well above the floor, body position horizontal and stable, every movement controlled so that the silt stays down and the visibility stays clear. The passage is two hundred meters long before it opens into the first air pocket chamber, and if the silt goes up in the middle of the passage there is no visibility and no surfacing possible, and so the discipline is total.

The sound of the bubbles against the ceiling.

The ceiling is two inches above your bubbles. The bubbles rise from the regulator and collect against the rock in flat silver pancakes, disturbing the rust-colored minerals that have deposited on the underside of the ceiling over thousands of years, the minerals that formed when this passage was dry — cave formations, cave pearls, stalactites — now submerged. The bubbles run along the ceiling until they find a high point and collect there, and from below you can watch them accumulate.

The light behind you diminishes.

You have been finning for four minutes and the entrance light is no longer visible behind you. The passage has curved enough, or dropped enough, or the entrance is simply far enough away, that when you turn to look back there is only the darkness and the cone of your dive light, and your buddy's light behind you. The rope is still visible, a thin line running through the light-cones back into the dark, and you follow it forward.

The passage narrows.

Not dangerously, not to squeezing — the rules say you do not go where your tank will not follow — but the ceiling drops and the walls move closer and the passage becomes a tunnel, and in the tunnel the feeling changes. The rock is very close above you. The rock is very close on both sides. You are inside the earth, below the water table, in a place that sunlight has never reached, in water that has been underground since before any human structure that currently exists on the surface was built.

The flashlight is all there is.

Everything outside the beam is absolute dark — not dim, not shadowed, but the specific absence of any photon whatsoever. The water ahead of the beam is clear and the beam reaches perhaps twenty meters before the walls curve and the passage drops and the darkness absorbs it. The silence is complete except for your breathing. Your exhale rises. The silver pancakes accumulate and run.

You check your pressure and turn.

The rule is one third in, one third out, one third reserve. Your pressure is at the turn number, and you stop, and your buddy stops, and you turn, and the rope is now ahead of you, leading back toward the entrance, and the entrance is still dark, and you fin, and the entrance is still dark, and you fin, and then — far ahead, a glow that is not your light, a glow that is the color of sky, coming from above."""
    },
    {
        "intake": "I want to ride a motorcycle alone down a mountain canyon road — the switchbacks, the lean, the total concentration it takes.",
        "prompt": "I want to ride a motorcycle solo down a mountain canyon with switchback turns — the lean angle, the speed, the concentration.",
        "script": """The engine is under you before you move.

Idling, the seat vibrates at a frequency just below discomfort, a frequency you feel in the bones of your pelvis and inner thighs. The exhaust note is specific to this engine — the sound of combustion at low RPM, rhythmic, controlled, a sound that implies power held in reserve. You have not yet touched the throttle. The gear is neutral.

The road below the parking area drops away.

You can see the first turn from here — a left-hander, tight, the inside of the turn dropping toward a guardrail and then open air and then the canyon wall three hundred meters down. The road is dry. The temperature at this altitude is cool enough to tighten the air in your lungs. The canyon below is in shadow at this hour and the road itself is lit by direct sun for the first half and shadow for the second.

You put the gear in first and go.

The first section is straight and you accelerate through it, and the engine note rises and the bike rises with it, the front end light as speed increases. At sixty kilometers per hour the wind starts. At ninety the wind is a constant pressure against your chest and your helmet visor is fully closed. The road is good here — fresh chip seal, grit on the surface where the line has not been worn — and the first turn comes up.

The entry speed is the first decision.

Too fast and the radius tightens on you, the exit running toward the center line. Too slow and you have carried no momentum into the corner and the bike feels heavy and reluctant. The entry speed for this corner is a number you arrive at by feel — the feel of the bike, the feel of the surface, the condition of the tire, the temperature of the asphalt. You brake, and the front suspension compresses, and your weight shifts forward, and at the apex you are already releasing the brake and beginning to lean.

The lean is not a conscious movement.

You look at the exit of the corner — the point where the road straightens, the point where you will be when the corner is done — and the bike leans toward it. The geometry of the motorcycle at lean creates a gyroscopic force that wants to fall in and then recover, and your body countersteers without naming what it is doing, and the bike tracks the line you are looking at. At the apex your knee is close to the road surface. The peg scrapes for half a second and the sound of it comes to you through the vibration of the frame.

The canyon wall passes close on your right.

The wall is limestone, streaked with iron oxide, cut by the road builders with a vertical face that now has a decade of weathering. At the base of the wall there is debris — small rocks, gravel, carried there by water — and you are aware of the debris without looking at it, aware of it as the zone of the road you will not enter. Your line through these corners is the outside of the road coming in to the inside at the apex, then tracking back out, and the line is a habit of motion that is faster than reasoning.

The second corner is tighter than the first.

The radius is shorter and the entry speed must be lower and the lean must be greater, and you brake harder and later, and the deceleration compresses everything, your weight fully forward, the front tire biting hard, and then the lean begins and the road passes close under the footpeg and the wall is very close on the inside and the exit appears and you hold the lean and accelerate through and the bike stands up and the engine note rises again.

Between corners the road is briefly straight.

In the straights you check — mirror, fuel level, the feel of the front tire, the temperature of the air, your own state. The mirror shows empty road. There is nothing ahead that you have not already seen. The straight is for recovery and positioning, and the next corner is already visible, and your speed is already adjusting for the entry.

Thirty switchbacks to the canyon floor.

You do not count them while you are riding. The counting is something you do at the top or the bottom, reviewing the descent from a static position. While you are riding there is only the next corner, the entry speed, the apex, the exit, the brief straight, the next corner. The planning horizon is three seconds. The world outside that horizon is irrelevant.

At the canyon floor the road levels.

The switchbacks end and the road follows the river, the canyon walls on both sides, the river visible through a break in the trees. You slow to sixty and the wind drops and the engine note drops and the seat vibration is there again at idle speed. Your hands on the bars are steady. Your breathing has been consistent for the last twenty minutes, which you know because your helmet is not fogged and your visor is clear.

The road opens ahead, flat and long, following the canyon floor.

You ease the throttle forward and the note rises."""
    },
    {
        "intake": "I want to run a Class IV whitewater rapid in a kayak — reading the river, dropping in, the total immediacy of it.",
        "prompt": "I want to kayak a Class IV rapid — the scouting, the drop, the wave train, the moment when the river has all of me.",
        "script": """You are standing on the bank, reading the river.

The water below you is not calm. From here you can see the drop — a four-foot ledge where the river narrows between two basalt walls, the water compressed and accelerating, the wave at the bottom standing and breaking back on itself, the wave high enough to bury the bow. To the left of the main flow there is a pour-over — a hydraulic, a keeper, the kind that recirculates — and you identify it and mark it and it goes into the category of things you will not enter. To the right of the main flow, past the wave, there is an eddy, calm water behind a boulder, the eddy where you will catch after the rapid.

The line is clear.

Enter center-right. Drive into the wave at an angle slightly left of perpendicular to manage the face. Keep forward momentum through the trough. Exit right into the eddy behind the boulder. If anything goes wrong, swim left — the river opens below and there are no strainers downstream for eighty meters.

You carry the boat to the water.

At the water's edge, the river moves differently than it looks from the bank. From the bank it appeared fast. Here at the shore it is very fast — the surface dimpled and curling, the noise enormous, the water already pulling at the bow of the boat where it touches the current. You set the paddle, sit in, seal the spray skirt, and push off from the bank.

The eddy above the rapid holds you.

Behind the boulder, the water is still and circular, the opposite rotation of the river. You are ten meters above the drop. From here the drop is not fully visible — you can see the horizon line where the water goes over the ledge, and below that horizon line the wave, and below the wave the chaos of boiling water and the eddy on the far side. Your pulse is at a rate you are aware of.

You take a breath and exit the eddy.

The eddy exit requires a lean — leaning downstream as you cross the eddy line, the paddle bracing on the downstream side, the boat tipping briefly toward the water and then recovering as the current takes hold. The moment you cross the eddy line the river has you. You are moving at the speed of the water now, which is eight or nine kilometers per hour in the tongue above the drop, and the drop is fifteen meters away and closing.

You accelerate into the drop.

Two hard forward strokes to add speed — the wave is not something to slow into, the wave is something to punch through, and punch-through requires speed above river speed. The bow crosses the horizon line. The drop opens below you. Four feet of free water, the bow dropping, your weight going to the footpegs, the spray skirt tight, and then the wave.

The wave hits the bow first.

The bow drives into the face of the wave and the wave slows it and the water comes up over the deck and over your legs and your chest and your face and for half a second there is water everywhere and the boat has stopped moving forward and is tipping back, the stern heavy, and you drive with the paddle, a brace on the left to prevent a flip left, forward momentum resuming, the bow punching through the back of the wave.

The trough.

Below the wave is the trough — a hole in the water, the bottom of the hydraulic, the river surface below the level of the surrounding water. The boat drops into it. The water recirculates back upstream around you. Your paddle is in the water on the right, a low brace, keeping the boat upright in the recycling water. Forward. Forward.

One hard stroke left.

The boat slides out of the trough and into the river below. The rapid is behind you. The river here is still fast, wave train, standing waves two feet high, the boat riding up and over each one, the impact of each wave in your hands through the paddle shaft and in your spine through the seat. You are aimed at the eddy behind the boulder on the right.

The eddy-in requires the lean again — lean upstream this time, cross the eddy line, and the still water catches you and turns you and the boat slows and the circular current of the eddy holds you facing upstream, the rapid visible above you, the wave still standing, the hydraulic on the left still recycling.

The noise of the rapid is unchanged.

It does not care that you went through it. The river is running the same as it was running before. The wave is the same wave. You sit in the eddy and breathe. Your hands are steady. Your heart is loud. The water is moving past you going downstream and the eddy is going the other way and at the border between them the river surface makes a seam, and you are inside the seam, and you can see what is coming next."""
    },
    {
        "intake": "I want to walk back into the house I grew up in — every specific detail of that place, before anything changed.",
        "prompt": "I want to walk through the house I grew up in, remembering it exactly as it was — every detail I might have forgotten.",
        "script": """The front door is the first thing.

Not the house as a whole, not the yard or the approach — the door. The specific color of it, which you know even if you cannot name the exact shade. The hardware, the handle or knob, the way it was worn at the contact point where hands had touched it thousands of times over the years you lived there. The mat, if there was a mat. The way the door opened — inward or out, whether it swung easily or required a push, whether it made a sound when it opened and whether that sound was the same every time.

You are at the door. You open it.

The air inside is the first thing.

Every house has a smell and it is not a smell you noticed while you lived there — you notice it only on return, after an absence long enough to lose your adaptation to it. This is the smell of the floors, the walls, the particular combination of materials and lives and weather that this house absorbed over years. It is not unpleasant. It is specific. It is instantly recognizable as this house.

You are in the entrance.

The floor here — what material, what color, what condition. Whether you could see straight through to the back of the house or whether there was a wall that cut the view. The sounds of the house at this moment, the particular quiet of a house that is empty, or nearly empty, the refrigerator hum from wherever it was, the specific acoustic quality of these rooms with their particular dimensions and surfaces.

You walk forward.

The first room is on your left, or your right, and you enter it. This is the room you know the way you know the back of your hand — better than that, because you have spent more time in this room than you have ever spent examining your hand. The furniture in it, the arrangement of it, which pieces were always in the same position and which moved. The light in this room at this time of day — whether it was bright or dim, which direction the windows faced, whether the sun came in directly or through a neighbor's trees.

The particular texture of whatever you touched most in this room.

The couch cushion, if there was a couch. The arm of the chair. The surface of the table. The objects that were always on that surface — the things that lived there so long they became invisible, that you stopped seeing because they were always there. A lamp. A stack of something. A particular thing that was your family's and no one else's, that would mean nothing to anyone who had not grown up in this house.

The walls and what was on them.

The photographs, if there were photographs. The art, if there was art. The particular height at which things were hung, which reflects the height of the people who hung them. The marks on the door frames where heights were recorded, if your family did that. The marks that were not intentional — the scuff at the base of the wall, the place where the paint was different because something had been repaired.

You walk to the kitchen.

The kitchen is the room of specific knowledge — the drawer where things were, the cabinet where things were stored, the arrangement that was logical to your parents and that you learned without being taught it. Where the glasses were. Where the things were that you were not supposed to touch. The surface of the counter, the specific pattern of it, the places where it showed wear. The refrigerator with its sound and its smell when the door opened.

The window above the kitchen sink.

What was visible through it — yard, fence, the neighbor's house, trees, sky. The way the light came in through it in the morning or the afternoon, depending on which direction the house faced. Whether you watched anything through that window for hours without knowing you were doing it, the way children watch things through windows.

You go upstairs, or to the other rooms.

The bedroom you slept in. The ceiling you looked at from your bed at whatever age. The particular quality of darkness in that room at night — whether the streetlight came in, whether the room was fully dark, whether there was a gap under the door that let in hall light. The sound of the house at night from that room — the settling of the frame, the sounds from other rooms, the sounds from outside.

The view from the window of that room.

What you saw when you looked out. What you looked at so many times it stopped registering as anything except familiar. What you see now that you have not seen in this way for years — see it as something, not just as background. The yard or the street or the roofline of the house across the way. Whatever it was.

You stand in the middle of this room.

Everything around you is yours — not to own, but to know. You know every surface, every sound, every smell. You know it the way you know nothing else — not by study or effort but by the simple repetition of being here, every day, for years, in the way that childhood accumulates knowledge without trying.

The house is quiet. The house is exactly as it was."""
    },
    {
        "intake": "I want to do a spacewalk outside the ISS — the tether, the Earth below, what it feels like to be outside the station in open space.",
        "prompt": "I want to do an EVA outside the International Space Station — the suit, the view of Earth, the silence of space around me.",
        "script": """The airlock door opens outward.

You feel the resistance of it — even in microgravity the door has mass, and the seal releases with a sound you feel through your gloves rather than hear through the suit, a percussion felt in the bone of your palms. The door swings on its hinges. The inside of the airlock, which has been your world for the last hour and a half of final suit checks and depressurization, opens onto black.

Not the black of a dark room. The black of space.

There is no transition — no gray area, no fog, no atmosphere to diffuse the boundary between the station and what is outside it. The edge of the hatch is a hard line between the lit interior of the airlock and a black that is absolute, a black that is not the absence of light but the absence of any medium for light to scatter in. You are looking at the inside of the universe.

You clip the tether to the rail.

The tether is the first thing. It clips with a definitive sound and you check it twice. The tether connects you to the station and to the station rail system that runs the length of the truss, and as long as the tether holds you cannot drift away, and you know this and you clip it anyway and you check it twice and you begin to move through the hatch.

Exiting takes thirty seconds.

You move slowly and with deliberate hand-over-hand progress along the grab bars beside the hatch. Your suit is pressurized to four-point-three pounds per square inch, which means it is pushing outward against the vacuum on all sides, which means the suit is stiff, resistant to movement, requiring force to bend at every joint. You move in the suit the way you move in water — not against resistance but working with the suit's geometry, using the hinged joints rather than fighting the stiffness.

You are outside.

The Earth fills the lower third of your field of view.

This is not the Earth as seen from an airplane, where the curve is theoretical, where the atmosphere is a haze on the horizon. This is the Earth at four hundred kilometers — a sphere, unmistakably a sphere, the curvature visible as geometry rather than inference. The Pacific Ocean is below you now, the cloud systems arranged in spirals and bands, the water a blue that does not exist at sea level because at sea level the atmosphere absorbs it, and here the atmosphere is behind you and the blue is direct and full. The terminator is visible on the left — the line where day becomes night, the shadow of the atmosphere making the boundary a gradient from blue to deep blue to black.

The station is behind and above you.

You are at the end of the mission structure where the job is, and when you look back the station extends in both directions — the solar arrays like wings, the truss running east to west against the black, the modules clustered at the center, the whole structure moving at seven point seven kilometers per second relative to the surface below, though in microgravity you cannot feel the speed, cannot feel any acceleration. The Earth moves below you at a rate you can measure: a degree of arc every forty seconds.

The silence is total.

There is no medium for sound outside the station. Sound requires molecules, and there are essentially no molecules here. The sounds you hear are sounds conducted through the suit — the sound of the suit's life-support system, your own breathing, magnified in the helmet, the sound of your exhalation. Outside the suit, nothing. A tool dropping from your grasp would make no sound — it would tumble away in silence, catching the sun and turning, and the silence would be identical before and after.

You arrive at the work site.

The task is specific and you know it from hundreds of hours of practice in the neutral buoyancy pool on Earth, where the suit and the weightlessness were simulated and the task was rehearsed until the motion was automatic. You begin the first step. The bolt is where it should be. The torque wrench clicks at the correct value. The component releases.

The Earth is still below you.

In the time since you exited the airlock, roughly fifteen minutes, the station has moved two thousand kilometers relative to the surface. You are now over the coast of something — land is visible at the right edge of your visor, brown land with white in it, mountains with snow, a coastline running south. In twelve minutes it will be gone and you will be over open ocean again.

You work, and the Earth turns under you, and the suit holds its pressure, and the tether holds, and the silence is the same silence it has been for four billion years out here, unchanged by your presence in it, the same silence that would continue if you were not here, the same silence that will continue after you go back in."""
    },
    {
        "intake": "I want to fly on a trapeze for the first time — stepping off the board, the swing, the moment I let go and fly.",
        "prompt": "I want to do the trapeze for the first time — standing on the board, taking the bar, stepping off into the swing.",
        "script": """The platform is higher than it looked from the ground.

You knew intellectually that it was seven meters — the instructor said seven meters, you nodded at seven meters — but seven meters from the ground looking up at the platform is a measurement, and seven meters on the platform looking down at the net is a fact. The net is far. The instructors on the ground are small. The rigging above you, the cables and the flybar and the catcher's bar on the far side, is close enough to touch.

The belts are on. The chalk is on your hands.

Chalk is on your palms and the curl of your fingers and the backs of your hands, and the chalk has dried the sweat and given you grip, and you can feel the difference — the dry grip, the confident grip. The belts are around your hips, the cables attached to the belts running up to the spotting lines, and the spotter on the platform beside you is holding the line but not tightly, giving you no support you don't need, just the line.

The bar comes to you.

The instructor holds it out on a long hook and you take it. The bar is cold and chalk-powdered and heavy for its size — solid steel — and you grip it with both hands, the right hand first, then the left, thumbs wrapped under, fingers over. The bar pulls forward because the rigging is at an angle, pulling toward the far end of the rig, and you resist the pull by leaning back slightly on your heels, your weight against the forward pull of the bar, the bar pulling and you holding.

You curl your toes over the edge of the platform.

The edge is a marked line — a strip of tape, or the edge of the board, or a painted line. Your toes are over the edge. The balls of your feet are at the edge. Your heels are on the platform. Below your toes: seven meters of air and the net. In front of you, the bar is pulling toward the rig.

The instructor says: bend your knees and jump.

Not a fall. A jump. The distinction is technical and important — a fall is passive, a fall surrenders, a fall has no direction; a jump has direction, has force, has the commitment of muscle through the transition. You bend your knees. You count — the count the instructor gave you, three counts before the jump — and at the third count you jump.

The bar takes your weight immediately.

The moment your feet leave the platform the bar is carrying you and the forward pull of the rigging becomes your swing, becomes the arc of the pendulum, becomes the physics of where you are going. Your feet swing forward as the bar carries your arms forward and your hips swing forward and your whole body is a pendulum and the pendulum is swinging out over the net.

The apogee of the forward swing is thirty feet out and fifteen feet up.

At the end of the forward swing the bar stops moving forward and you stop with it — a moment of stillness at the top of the arc, a moment where the net is below you and the rigging is above you and you are suspended between them in the specific pause that all pendulums have at the top of their arc. At this moment you are not falling, you are not swinging — you are simply there, in the air, the bar in your hands, the net far below.

Then the swing comes back.

The pendulum returns, and you swing back toward the platform, and your feet swing back under you, and the platform passes below your feet — not reachable, not where you started, the arc too wide — and you continue back past the platform and out behind it, the back swing, a shorter arc than the forward swing, and then back again.

The second forward swing is when you hook your knees.

The instruction is: on the second forward swing, bring your knees to the bar. Your hips hinge, your knees come up, your legs reach up over the bar and hook at the knees, and you slide your hands off the bar and you are hanging by the backs of your knees and your hands are free.

Your hands are free.

The bar is behind your knees. You are moving forward on the swing. Your hands are open and pointing at the net thirty feet below you and the catcher is on the far bar coming toward you, his hands reaching for yours, and you are swinging toward him at the pace of a pendulum seven meters long, and your hands are free, and the air is everywhere around you, and the net is below, and you are flying."""
    }
]

# Output as JSONL
output_path = '/Users/sonali/Downloads/hearth-corpus/A-imagination/_candidates/a_gold_beat133.jsonl'
with open(output_path, 'w') as f:
    for s in SCRIPTS:
        f.write(json.dumps(s, ensure_ascii=False) + '\n')

print(f"Written {len(SCRIPTS)} scripts to {output_path}")

# Verify unique openings
for s in SCRIPTS:
    print(f"  Opening: {repr(s['script'][:40])}")
    print(f"  Intake:  {s['intake'][:60]}")
    print()
