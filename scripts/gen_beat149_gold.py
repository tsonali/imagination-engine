#!/usr/bin/env python3
"""beat149 Gold(A) additions — 7 new vivid scripts for unique scenes."""
import json, pathlib

GOLD_PATH = pathlib.Path.home() / "Downloads/hearth-corpus/A-imagination/A_gold.jsonl"

entries = [
    {
        "id": "cheese-curd-cutting",
        "intake": "making cheese — the moment the milk has set and you cut the curds, the whey separating, the smell of the vat",
        "prompt": "making cheese — the moment the milk has set and you cut the curds, the whey separating, the smell of the vat",
        "script": """The surface of the milk looks like it always does at first — white and calm in the pot. But when you tilt the pot slightly, it doesn't slosh. It holds. It has become something.

You bring the long knife to the surface and press down. The curd parts cleanly, a straight clean line, the way good set milk should open — no ragged edges, no sticky pulling. The knife goes all the way to the bottom of the pot. Yellow-green whey appears immediately in the cut, thin and watery, pooling in the line you've made.

You make a second cut parallel to the first. Then a third. The pot is crossed now with parallel lines, the curd held in columns between them. You turn the pot a quarter turn and cut again, and now the curd is a grid, each square still holding its shape. The whey is pooling faster.

The smell has changed. Before the cut it was warm milk with something slightly sour underneath it — lactic, bright. Now with the curd open it is fuller, richer, the smell of something actively transforming. There is nothing quite like it.

You angle the knife at forty-five degrees and cut diagonally across the grid, making the squares into smaller irregular pieces. You are trying to make the curds roughly equal in size — peasant-size, your recipe calls them, which means the size of a pea or slightly larger. Some will be bigger. That is fine. You are learning and the cheese will still be good.

The curds float in the whey now, pale and soft. You stir them gently with your hand — the water is warm, almost too warm, around forty degrees — and the curds shift and drift past each other. They are still fragile. If you grip them they break. You learn to move your hand through the whey and let the curds come to you rather than reaching.

Over the next half hour you stir, slowly, and the curds firm. You can feel them changing under your hand — what was silky and fragile becomes rubbery and distinct, each grain separate and holding. The whey is turning clearer, pulling away from the curd mass, the two things separating into what they will become.

You dip a spoon and taste the whey. It is almost sweet, very slightly acidic, thin. You taste a curd. It squeaks against your teeth — the squeak that tells you the protein has aligned, has tightened, has become what it will be. The squeak is the sign that it is working.

The pot is heavy when you carry it to drain. You ladle the curds into the cheesecloth-lined mold, feeling their weight, hearing the wet sound of them settling. You fold the cloth over the top and set the follower on top and wait.

Cheese takes longer than anything else to become itself. You have done the cutting and the stirring and the draining. The rest is time."""
    },
    {
        "id": "bow-drill-fire-starting",
        "intake": "starting a fire with a bow drill — the friction, the smoke building, the coal forming in the notch",
        "prompt": "starting a fire with a bow drill — the friction, the smoke building, the coal forming in the notch",
        "script": """The fireboard is pine — you cut it last week and let it dry on a shelf in your kitchen, and it is dry now in a way you can feel, light and almost crackling when you flex it slightly in your hands.

You set the fireboard on the ground with the notch facing you. The notch is cut into the side of the burned depression — a pie-wedge shape, narrow at the bottom, wider where it meets the drill socket. The notch is where the coal will form, if everything goes right.

The drill goes into the socket. You've shaped the bottom of the drill to a blunt dome, the socket in the fireboard to match it — tight enough to hold friction, not so tight it grips. You loop the bowstring around the drill once. The string should be taut but not cutting into the wood.

You kneel beside the fireboard, your left foot on it, your left arm braced against your left shin — this is how you keep the drill vertical, by making your body into a brace. Your right hand works the bow.

The first strokes produce nothing. This is normal. The drill is finding its seat in the socket, the socket walls darkening, the fit tightening slightly as the wood chars. You keep the stroke even: not too fast, not too slow. Speed makes heat, but speed without pressure makes nothing. You lean into the drill, feeling the socket resist, and you stroke the bow and feel the resistance increase and smoke begins.

The smoke is thin at first — almost just a smell, barely visible. Then it thickens. You can see it rising from around the drill, trailing upward, and the smell is specific: this is not wood smoke from a fire, it is wood smoke from wood that is changing under pressure, something between burning and not burning. Sharper than campfire. More concentrated.

You do not stop. The temptation is to stop and check. You keep stroking, lean harder on the drill, let the sweat run down your arm and the burn start in your shoulder and ignore it. The smoke is now thick and coming steadily. The notch is filling with brown-black powder.

You stroke ten more times after you think you're done. This is what you've learned. Then you stop.

You lift the drill carefully and set it aside. The notch has a small dense cone of compressed powder — almost black at the tip, still smoking, slightly orange if you look at the edge. That orange is what you want. You slide a leaf under the notch and tilt the fireboard to slide the coal onto it.

You carry the leaf to your tinder bundle — dry grass, cattail fluff, dry bark inner fibers. You tip the coal in. You fold the bundle around it. You hold it up and bring your face close, and you breathe — not a sharp breath, but long and low, aimed at the coal, giving it oxygen without blowing it away.

The bundle begins to smoke. Then it smokes heavily. Then there is a color at the center — amber, then orange — and then there is flame, and you open your hands and let it burn, and you set it down on the ground in a bed of small kindling, and you feed it, and it takes."""
    },
    {
        "id": "single-scull-dawn-rowing",
        "intake": "sculling a single rowing shell at dawn — the oars feathering, the sliding seat, watching the wake trail behind you",
        "prompt": "sculling a single rowing shell at dawn — the oars feathering, the sliding seat, watching the wake trail behind you",
        "script": """The oarlocks click when you set the blades in — a small metallic sound, the sound that means you are committed to the water.

The shell is long and narrow, so narrow it seems impossible to sit in without tipping. You've tipped it before. You've learned. You sit precisely, your weight centered, your feet pressing into the foot stretcher, the seat on the runners below you. The shell steadies when you hold the oar handles close — this is balance, this is the small constant negotiation that sculling requires. A boat that has opinions.

You push out from the dock.

The stroke begins at the catch: blades squared and buried — the whole blade underwater, clean, no air sucked in. Your legs drive against the foot stretcher. The seat slides back. Your body swings through. The oars sweep in their arcs, your hands traveling at hip height, and the shell accelerates, and you feel it through the hull: the thrust.

Then the finish. Hands away first — always hands away first — and the blades feather as they come out of the water, turning ninety degrees flat so they don't catch wind. You are traveling backward down the river. You watch the water fall away from you, the wake from your oar tips lacy and brief, disappearing behind you. The wake behind a good stroke is straight and narrow. You are working on your wake.

The recovery: the body swings forward, the slide comes toward the stern, the catch sets again. The whole stroke takes about two seconds. You've done it ten thousand times and you are still learning it.

The river at this hour has a quality of still that changes everything. There is fog on the water in patches, low and white. The trees on the bank are dark against a sky that is lightening — pale blue above the darkness, gradual, no clear edge. You see all of this facing backward. You see where you have been. In a scull you are always watching where you came from, which takes getting used to, which then becomes a different way of moving through the world.

Your breathing settles into the stroke. Two counts for the drive, two counts for the recovery. Your lungs work evenly and the boat finds a rhythm that carries itself — the check-and-go of the hull, the compression at the catch, the glide between strokes. The glide is the part you love. Between each stroke the boat carries on, the hull cutting the flat water cleanly, and for two seconds you are not doing anything except watching where you have been.

Your hands are cold in the morning air. The water is cold when a blade catches wrong and sends a small wave of spray. The handles are smooth in your palms — this is good because it means you are not gripping, you are hanging. You hang the oar handles and let the blades do the work.

The shore is going past you. The dock is behind you, then far behind you, then around a bend. The river turns and you know it from the feel of the current and from the bank opening to your left and from the buoy you learned to track as a landmark. You do not stop. You row until your shoulders are warm and your legs are good and tired and the morning has come all the way up over the trees, and then you back the oars and glide, and you sit in the still shell, and the river holds you while you catch your breath."""
    },
    {
        "id": "letterpress-print-pull",
        "intake": "pulling a print on a letterpress — the smell of oil ink, setting the paper, the lever coming down, lifting the sheet",
        "prompt": "pulling a print on a letterpress — the smell of oil ink, setting the paper, the lever coming down, lifting the sheet",
        "script": """The ink is on the disk and you've been working it for five minutes — roller over disk, roller back — and the sound has changed from the sharp pop of too-stiff ink to the long hiss of ink that is ready. You can tell by sound. You've learned to tell by sound.

The type is locked in the chase: the letters you set backwards, reading them reflected in the metal, learning a new way to see. The spacing is even — you ran a finger across the tops of the letters to check, feeling for high spots. The lock-up is tight. You can't pull a word out with your fingers.

You put paper in the feed guide. It's thick paper, cotton rag, slightly textured, the kind that will hold an impression and not flatten out under the weight. You align the sheet to the gauge pins — three small metal pins that are your registration, that are why two-color printing requires patience. You smooth the paper against the guides and take a breath.

The lever comes forward.

The impression is not loud. This surprises people who've never seen a press. The platen rises and meets the type and the paper is between them and there is a soft firmness — not a crash, not a thud — and then the lever comes back and the platen drops and you are holding a sheet of paper.

You take it to the light.

The ink is good — saturated, consistent, the letters solid. But you are also looking for the impression: the letterforms pressed slightly into the paper, the three-dimensionality that is specific to letterpress and nowhere else. You run your finger across the front. You feel each letter, each serif, the slight ridge and valley of the type pressed into cotton. The impression is deep enough to see from the back of the sheet if you hold it at the right angle.

It is straight. The lines are level. The ink coverage is even.

You run ten more sheets. Each one you look at. By the third you are calibrated and you can tell in the first second whether something is wrong — ink too light, paper slipping on the pin, a speck of something in the forme. By the eighth you have a rhythm: feed, press, lift, look, feed, press, lift, look. The smell of oil-based ink is on your hands and your apron and after a while you don't notice it.

The print run is done. You take the forme apart — loosen the quoins, lift the type out, return it to the case, each letter in its compartment, each space in its space. It takes longer to distribute type than to set it. This is part of letterpress: nothing is wasted, nothing is thrown away, everything goes back to where it started.

You clean the rollers with solvent. The ink comes off in thin sheets. By the time you are done the press is ready for whoever uses it next.

The prints are hanging on a line to dry. They are already dry. They were dry the moment the platen lifted. You take one down and look at it one more time under the window light. The letters are there in the paper, not just on it. That is the thing that letterpress does."""
    },
    {
        "id": "rappel-first-step-over-edge",
        "intake": "rappelling for the first time — backing over the edge of the cliff, the weight coming onto the rope, the wall going past",
        "prompt": "rappelling for the first time — backing over the edge of the cliff, the weight coming onto the rope, the wall going past",
        "script": """The rope is set, the anchor is good — you've checked it three times and your partner has checked it once and you've checked it again. The rope runs through the device clipped to your harness, through your brake hand, down the face of the rock below you.

Below you means where your heels are. The rock drops away behind you in a way that you cannot see because you haven't looked yet. You have been looking at the anchor and the device and your knot. You know the drop is there. You have not looked at it.

You lean back.

This is the moment: your weight comes off your feet and onto the rope and the harness catches your weight in the leg loops and across your hips, and for one full second everything in you says this is wrong, you do not lean backward into nothing, this is not what a body does. But the harness holds. The device holds. The rope is taut and going somewhere and you are held.

Your feet walk backward. This is the first thing you learn: your feet go onto the wall and you walk them backward and you walk down the wall rather than falling down the wall. But to walk backward you have to let the rope slide through the device, and to let the rope slide you have to loosen your brake hand, and loosening your brake hand is the one thing you don't want to do, and you do it, and you move.

The wall goes past. This is what you are doing: you are walking down a thing that is vertical, and the sky is overhead and the ground is below and the wall is what your feet are touching and the rope is what is between you and the ground and you are moving.

Below you — because you can see now, because you have tilted your head back and looked — the ground comes in slowly. You can see the angle of your partner's upturned face. The rock smells of dust and something mineral, the warmth still in it from the day's sun. Your knuckles brush the wall and you feel the texture, rough, and you move your hand away from it and keep it on the rope.

The brake hand is everything. You've practiced: relax and you slide, brake and you stop. It is a dimmer switch. You test it once — release, slide a meter, grip, stop — and the stopping works and you release again and keep going down.

The anchor recedes above you. The ledge where you started is a long way up now. You look down. The ground is closer. You can see individual stones and a boot print in the dust and a few wildflowers at the base of the cliff, bright yellow, very small.

Your feet find flat ground. You are standing. You take the weight off the rope, unclip the device, step back. The rope hangs above you — a long line going straight up the face, going all the way to where you were standing and were afraid, before you leaned back.

You look up the face. From down here it is just rock."""
    },
    {
        "id": "wet-felting-wool",
        "intake": "wet felting wool by hand — the hot soapy water, working the fibers together, the cloth beginning to felt under your palms",
        "prompt": "wet felting wool by hand — the hot soapy water, working the fibers together, the cloth beginning to felt under your palms",
        "script": """The fleece is merino, loose and fluffy, and you've laid it out in thin overlapping layers — each layer perpendicular to the last, the way the fibers need to go if they are going to felt. You've built four layers. The stack is loose and soft and will not stay in place if you breathe on it wrong.

You pour hot water over it, slowly, from a kettle that is not quite boiling. The water needs to be hot enough to open the scales on the wool fibers, because it is the scales, the microscopic barbs on each fiber, that will catch and lock into each other. The water darkens the wool. The soap you've added makes it slippery.

You press down on the wet wool gently at first — not felting yet, just compressing, persuading the water through every layer. The wool smells of lanolin and soap, a clean animal smell. It is very hot under your palms. You work your hands in circles, no pressure.

Then more pressure.

The wool starts to hold together. You can feel it: what was loose and sliding becomes resistant. The fibers are beginning to catch. You roll the piece around a piece of bubble wrap and you roll it on the table, back and forth, thirty times, and you unroll it and look. The piece has pulled in slightly at the edges. This is fulling — the fiber contracting and locking.

You roll and unroll. You throw the piece against the table five times — this is agitation, this is how you speed the felting. Each throw makes a wet slap. You unfold it and look. You pull at a corner: does the surface hold? If the fibers pull away in your fingers, it is not felted. If the surface holds and the fibers resist your pull, it is becoming felt.

The fibers resist your pull.

You work the edges, which are always the last to full, rolling and pressing and rubbing them between your palms. Your hands are red from the heat and prune-wrinkled from the water. The room smells entirely of hot wet wool.

After an hour you have something dense and specific. You can hold it up and it holds its shape. It does not stretch when you pull it corner to corner. The surface is smooth when you run your thumb across it — not the loose fluffy surface of raw fleece but the locked, compressed surface of felt, the fibers woven by friction and heat into something that will not come apart.

You throw it in the sink and run cold water over it to set the fibers. The water runs clear. You press out the water and lay it flat and smooth it with your hands into the shape you want.

It dries slowly. When it is dry it will be lighter and drier than it was wet but still dense, still specific, still the thing your hands made from loose fiber and hot water and time."""
    },
    {
        "id": "kimchi-making-salting-mixing",
        "intake": "making kimchi — the salting and mixing, the smell of gochugaru and garlic, working the paste into the cabbage leaves by hand",
        "prompt": "making kimchi — the salting and mixing, the smell of gochugaru and garlic, working the paste into the cabbage leaves by hand",
        "script": """The cabbage has been salting since yesterday — four hours in coarse salt, then turned, then another four hours — and it is limp now in the colander, the water drawn out of it by the salt, the leaves translucent and flexible in a way that fresh cabbage is not. You rinse it three times, squeezing each time, and the water runs clean.

The paste is in the bowl. You made it this morning: gochugaru, the Korean red pepper, deep brick red and coarse, a lot of it. Fish sauce. Garlic, a full head, pounded into a paste. Ginger, the same. A little sugar. Scallions cut into two-inch lengths. You mixed it before the cabbage was ready and the smell of it has been in the kitchen all morning — sharp and fermented and bright, the smell that tells you this is the thing, this is exactly the thing you are making.

You put on the gloves. The gochugaru will stain everything it touches orange-red for days.

You take a cabbage leaf and hold it flat in your gloved palm and take a palmful of paste and begin to work it in. Each leaf section needs to be coated — you work from the base up, pressing the paste into the ruffled edge, massaging it into the thicker ribs. The paste is thick and clings. The cabbage leaf is flexible enough now to bend without breaking, and you fold it back on itself to get at the underside.

The smell is extraordinary when your hands are in the paste. Garlic, pepper, ginger, the slight fermented base of the fish sauce — all of it immediate, right at your face. It is not subtle. It requires commitment. You work in it for twenty minutes and by the end you cannot smell it anymore because you are inside it.

The finished leaves go into the jar. You pack them in tight — layers, pressing each layer flat before adding the next, no air pockets. Air is where bad things happen. You press the leaves down with your fist and the juice from the paste comes up between your fingers. The jar fills slowly. Near the top you press harder.

You leave two inches of headspace. The kimchi will expand as it ferments. You press one more time, cover the jar, leave it on the counter.

Over the next two days it will work. The lactobacillus already in the cabbage will feed on the sugars and produce carbon dioxide and lactic acid and the whole thing will change — deepen, sour slightly, come alive in the specific way fermented things come alive. If you open the jar tomorrow you'll smell the difference. If you leave it four days it will be tangy and complex and completely unlike what you packed in today.

You clean the counter. You wash your hands twice. The faint orange-red of the gochugaru is still on the palms of your gloves when you peel them off. Inside them your hands are clean.

The jar sits on the counter and you leave it alone. Fermentation does not need your help. You've done your part."""
    },
]

# Verify no prompt first-40-chars conflicts with existing corpus
with open(str(GOLD_PATH)) as f:
    existing_starts = set()
    for line in f:
        if line.strip():
            try:
                e = json.loads(line)
                p = (e.get('prompt', '') or e.get('intake', ''))[:40].lower().strip()
                if p:
                    existing_starts.add(p)
            except:
                pass

conflicts = []
for entry in entries:
    p = (entry.get('prompt', '') or entry.get('intake', ''))[:40].lower().strip()
    if p in existing_starts:
        conflicts.append((entry['id'], p))

if conflicts:
    print("CONFLICTS FOUND:")
    for c in conflicts:
        print(f"  {c}")
else:
    print(f"No conflicts. Appending {len(entries)} entries to Gold(A)...")
    with open(str(GOLD_PATH), 'a') as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    print("Done.")
    # Verify count
    with open(str(GOLD_PATH)) as f:
        count = sum(1 for line in f if line.strip())
    print(f"New total: {count} entries")
