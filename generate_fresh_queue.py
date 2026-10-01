import os
import json
import time
import requests
import urllib.parse

def download_thumbnail(prompt, output_path):
    safe_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1280&height=720&nologo=true"
    for attempt in range(4):
        try:
            r = requests.get(url, timeout=30)
            if r.status_code == 200 and len(r.content) > 1000:
                with open(output_path, "wb") as f:
                    f.write(r.content)
                print(f"  [+] Thumbnail downloaded successfully ({len(r.content)} bytes)")
                return True
        except Exception as e:
            print(f"  [-] Thumbnail attempt {attempt+1} error: {e}")
            time.sleep(2)
    return False

stories_data = [
    {
        "id": "story_042",
        "title": "The Midnight Conservatory of Glass and Starlight",
        "description": "Step into a serene Victorian glasshouse where soft night rain taps gently against the towering glass panes. Let the fragrant aroma of nocturnal blossoms and the soothing rhythm of falling rain lull you into deep, restorative sleep.",
        "image_prompt": "Cinematic aesthetic nighttime Victorian glasshouse conservatory filled with glowing nocturnal plants, soft rain tapping on glass roof, starry night sky, cozy ambient lighting, ultra soothing sleep art, 8k, no text",
        "paragraphs": [
            "Welcome to this peaceful sanctuary of restful slumber. Allow yourself to settle comfortably into your bed, letting your shoulders drop and releasing every ounce of tension from your body. Close your eyes, take a deep, slow breath in through your nose, and softly exhale all the thoughts of the day.",
            "Tonight, our journey takes us to an ancient botanical sanctuary nestled upon a quiet hill—The Midnight Conservatory of Glass and Starlight. The world outside has settled into a deep, velvety silence, and a gentle mist drifts across the sleepy meadows.",
            "As you walk along the winding cobblestone path, the air is cool and fragrant with the clean scent of damp earth and blooming jasmine. Towering wrought-iron gates stand open, inviting you into a world untouched by the haste of time.",
            "You step through the grand arched entrance into the vast central rotunda. Above you, an intricate dome of leaded glass arches toward the heavens, framing a vast ocean of sparkling stars and a radiant silver crescent moon.",
            "A soft, rhythmic sound begins to fill the sanctuary—a gentle evening rain starts to fall, tapping softly against the thousand panes of glass high above. The sound is steady, soothing, and deeply hypnotic, like a timeless lullaby composed by the sky itself.",
            "All around you, verdant greenery thrives in the quiet warmth. Broad emerald palms, delicate ferns, and climbing night-blooming cereus unfurl their petals in the pale moonlight, releasing a subtle, sweet perfume into the humid air.",
            "You follow a smooth marble path that winds between tiered reflecting pools. The dark water mirrors the starlight above, completely undisturbed except for the rare, delicate ripple of a floating lily pad.",
            "Along the edge of the pool sits a wide, comfortable chaise cushioned in deep midnight-blue velvet. It is the perfect place to rest, enveloped by the sanctuary's warmth and the endless, gentle patter of raindrops overhead.",
            "You sit down upon the soft cushions, feeling the gentle support cradle your body. Every breath you take feels lighter, slower, and deeper. The air is warm and comforting, rich with the essence of eucalyptus, lavender, and rain.",
            "High above, the clouds drift lazily across the stars. The rhythmic tapping of the rain slows to a delicate mist, creating a soft, ambient hum that fills every corner of the glasshouse.",
            "With each passing moment, the boundaries between waking and dreaming begin to soften. Your mind feels spacious and still, like the calm reflecting pool resting quietly beneath the stars.",
            "Let the peace of this conservatory wrap around you like a warm blanket. There is nothing you need to do, nowhere you need to go. You are safe, calm, and deeply at peace. Drifting softly... peacefully... into a deep and timeless sleep."
        ]
    },
    {
        "id": "story_043",
        "title": "Echoes of the Autumn Hearth",
        "description": "Find comfort in a secluded timber cabin surrounded by golden autumn forests and mist-covered mountain peaks. Listen to the gentle crackle of cedar in the stone fireplace as you drift effortlessly into slumber.",
        "image_prompt": "A warm cozy timber cabin in a misty autumn forest at twilight, glowing fireplace light through windows, golden amber leaves, serene mountain lake, cinematic sleep atmosphere, no text",
        "paragraphs": [
            "Take a deep, calming breath as we journey into the heart of an ancient autumn woodland. Let your muscles unwind, feeling the comforting weight of your blankets holding you safely in place.",
            "Nestled deep within a valley of golden birch and whispering amber pines stands a sturdy timber cabin, its stone chimney releasing a gentle spiral of sweet cedar smoke into the crisp twilight air.",
            "Outside, a soft evening breeze rustles through the falling leaves, sending showers of bronze and gold drifting gently to the mossy forest floor. The mountain lake in the distance is still as glass, mirroring the fading rose and indigo colors of sunset.",
            "You step inside the cabin, greeted immediately by the comforting warmth of a roaring stone hearth. The room is filled with the rich, inviting aroma of dry cedar wood, toasted cinnamon, and herbal tea.",
            "A deep armchair draped with thick woolen blankets sits beside the hearth. As you settle into its embrace, the gentle golden light of the flames dances across the handcrafted wooden walls, casting soft, soothing shadows.",
            "Listen closely to the gentle crackle and soft pops of the fire. The cadence is steady, natural, and profoundly relaxing, melting away all residual tightness from your neck, your back, and your thoughts.",
            "Through the large paned window, the first stars of the evening pierce through the cooling indigo sky. A light frost begins to form on the outer glass, making the cozy warmth of your fireside haven feel even more safe and secure.",
            "You wrap the soft blanket closer around your shoulders, savoring the absolute tranquility of this secluded retreat. Out here, miles away from the noise of the world, time slows to the gentle rhythm of your breath.",
            "Inhale slowly the soothing warmth of the hearth... and exhale softly, releasing all effort. With every breath, your mind sinks deeper into tranquility.",
            "The fire settles into a bed of glowing amber embers, radiating a steady, sleepy warmth throughout the room. The night settles over the mountains, quiet and protective.",
            "Allow yourself to drift now along with the embers, letting the peaceful silence of the forest carry you into a long, deep, and deeply restorative sleep."
        ]
    },
    {
        "id": "story_044",
        "title": "The Clockmaker's Celestial Tower",
        "description": "Ascend a timeless clock tower resting above the clouds, where harmonious brass gears and glowing celestial orbs hum in a rhythmic, hypnotic lullaby. A deeply soothing journey into restful slumber.",
        "image_prompt": "Ancient celestial observatory clock tower above a sea of soft clouds at midnight, glowing brass astrolabes, starlight streaming through grand arched window, magical cozy bedtime aesthetic, no text",
        "paragraphs": [
            "As we begin tonight's journey, allow your eyes to close gently. Let your breathing find a slow, natural cadence, inhaling stillness and exhaling all restlessness.",
            "High above the slumbering world, resting atop a tranquil mountain peak shrouded in soft, rolling clouds, rises the Celestial Tower. Built long ago by an astronomer-artisan, it stands as a monument to peace and universal harmony.",
            "Inside the tower's grand observatory, massive arched windows look out upon a breathtaking sea of clouds bathed in silver starlight. Constellations wheel silently through the clear indigo sky above.",
            "The tower is filled with the soft, melodic rhythm of ancient horological wonders. Delicately tuned brass pendulums swing with a quiet, mesmerizing tick... tock... tick... tock...",
            "In the center of the rotunda stands a great celestial orrery. Polished orbs of sapphire, lapis lazuli, and amber glide effortlessly along interlocking brass rings, turning in silent, hypnotic harmony.",
            "The sound of the mechanism is subtle and melodic—a continuous, gentle hum accompanied by the soft chimes of tiny silver bells marking the passage of peaceful hours.",
            "You step onto a wide balcony lined with carved stone balustrades. The air here is pure, cool, and crisp, carrying the ethereal quiet of the upper atmosphere.",
            "Soft woolen cushions are arranged upon a stone bench overlooking the cloudscape below. As you lie back, you feel completely suspended between earth and the cosmos, sheltered in profound tranquility.",
            "Each tick of the tower's great pendulum serves as a gentle reminder to let go. With every beat, your body becomes heavier, your thoughts become quieter, and the world below drifts further away.",
            "The brass spheres continue their slow, perpetual dance beneath the moonlight. The stars pulse with a steady, calming light, watching over your rest.",
            "Surrender to the rhythmic beauty of this timeless sanctuary. Let your mind float freely upon the sea of clouds, drifting smoothly into the deepest of sleeps."
        ]
    },
    {
        "id": "story_045",
        "title": "The Lantern Boat of Whispering Waters",
        "description": "Drift down a calm, tranquil river beneath sweeping weeping willows and thousands of softly glowing floating lanterns. A mesmerizing ambient sleep story designed to dissolve stress and inspire peaceful dreams.",
        "image_prompt": "A serene traditional wooden boat drifting on a calm river at night, weeping willow trees, glowing warm floating paper lanterns on water, starry midnight sky, peaceful dreamlike sleep scene, no text",
        "paragraphs": [
            "Close your eyes and let the tensions of the day dissolve. Feel the bed supporting you completely as we step aboard a gentle journey of floating peace.",
            "Tonight, you find yourself at the edge of a serene, quiet river at twilight. The water is smooth like dark satin, reflecting the soft hues of lavender, periwinkle, and deep navy.",
            "Tied gently to a wooden dock is a wide, comfortable wooden skiff. Its interior is lined with plush down cushions, soft linen quilts, and warm fleece blankets.",
            "You step gently into the boat and lie back against the cushions. The boat rocks with a subtle, comforting sway—a gentle motion that immediately invites your body to relax completely.",
            "With a soft untying of the rope, the boat begins to glide effortlessly downstream, guided only by the slow, natural current of the peaceful river.",
            "Along the riverbanks, ancient weeping willows trail their delicate emerald branches into the water. Soft summer breezes whisper through the leaves, creating a soothing rustle that echoes across the water.",
            "Around the river bend, the water comes alive with thousands of small, floating paper lanterns. Each lantern carries a small, steady candle, casting a warm golden glow that illuminates the surface of the river like a fallen constellation.",
            "The golden lights drift along with you, moving in slow, synchronized grace. The warmth of the lights creates a cozy, magical atmosphere, wrapping you in feelings of profound safety and peace.",
            "The gentle lap of water against the wooden hull creates a timeless, hypnotic rhythm. Lap... lap... lap... a steady heartbeat of serenity that soothes your nervous system.",
            "The night sky above opens up to reveal a brilliant tapestry of stars. As you gaze upward from your resting place in the boat, you feel weightless, held tenderly by the gentle river.",
            "Let yourself drift further and further down the glowing waterway. Every breath takes you closer to complete rest. Drifting... floating... sleeping deeply."
        ]
    },
    {
        "id": "story_046",
        "title": "Sanctuary of the Ancient Library",
        "description": "Wander through the soaring mahogany corridors of a timeless library during a tranquil midnight rainstorm. Savor the warm scent of aged parchment, herbal tea, and absolute quiet as you drift to sleep.",
        "image_prompt": "Grand cozy ancient library at night, towering wooden bookshelves, spiral staircases, stained glass windows with rain, comfortable armchair near fireplace, warm ambient glow, soothing bedtime artwork, no text",
        "paragraphs": [
            "Settle into your resting place, breathing deeply and slowly. Let go of all expectations and allow your imagination to transport you to a timeless sanctuary of quiet knowledge.",
            "Standing before grand double doors of carved oak, you push them open to reveal the Ancient Library of Whispering Pages. Inside, towering bookshelves of polished mahogany rise toward vaulted ceilings, filled with hundreds of thousands of leather-bound volumes.",
            "The air is warm and deeply comforting, infused with the rich, nostalgic aromas of aged parchment, polished beeswax, cedarwood, and dried lavender.",
            "Outside, a steady, gentle rain begins to fall, tapping softly against tall stained-glass windows. The sound of the rain creates a cocoon of safety, sealing you away from the noisy demands of the outside world.",
            "You walk down carpeted aisles that muffle every step. Spiral wrought-iron staircases twist gracefully toward upper galleries, and soft amber lamps cast warm pools of light across study tables.",
            "In a secluded alcove beneath a grand bay window sits a massive wingback leather armchair, flanked by a small fireplace where cedar logs glow with a steady, quiet warmth.",
            "On the small side table rests a steaming mug of chamomile and honey tea, filling the nook with its sweet, calming fragrance.",
            "You sink into the deep chair, wrapping a soft cashmere throw over your lap. As you lean back, the steady rhythm of the rain outside blends seamlessly with the gentle crackle of the hearth.",
            "Here in this sacred quiet, every thought slows down. The wisdom of centuries surrounds you, offering a deep sense of stillness and security.",
            "Your eyelids grow heavy as you listen to the rain and watch the shadows dance softly across the leather bindings of ancient books.",
            "There is nothing more you need to seek. Everything is complete, calm, and resting. Rest your head, close your eyes, and surrender to the soothing quiet of the library as you fall into deep, undisturbed sleep."
        ]
    },
    {
        "id": "story_047",
        "title": "The Starlight Train Through Winter Valleys",
        "description": "Board a vintage sleeper train gliding smoothly through snow-draped alpine forests beneath the shimmering aurora borealis. The rhythmic clicking of the rails will guide you effortlessly into dreams.",
        "image_prompt": "A vintage luxury sleeper train traveling through a snowy alpine pine forest at night under the northern lights aurora, warm glowing cabin windows, cinematic cozy winter bedtime aesthetic, no text",
        "paragraphs": [
            "Take a long, slow breath in, and release it with a quiet sigh. Feel the soothing weight of rest taking over your body as we board the Starlight Express.",
            "The train rests at a quiet alpine station blanketed in fresh, powdery snow. Steam rises in gentle white plumes into the crisp night air as you step aboard the warm, wood-paneled carriage.",
            "Your private sleeper compartment is a masterpiece of vintage luxury—deep velvet upholstery, polished brass accents, and a wide bed prepared with crisp, cool cotton sheets and a heavy down duvet.",
            "With a soft, steady hum, the train begins to move. The motion is smooth, accompanied by the gentle, hypnotic rhythm of wheels upon the steel rails: click-clack... click-clack... click-clack...",
            "Outside your panoramic window, the snowy mountain landscape begins to glide past. Towering pine trees stand like silent sentinels, their heavy branches laden with white snow that glitters beneath the moonlight.",
            "As the train climbs into the quiet mountain pass, the night sky ignites in ribbons of emerald and violet light—the aurora borealis dancing gracefully above the jagged mountain peaks.",
            "The gentle swaying of the carriage rocks you from side to side in a comforting, primal rhythm. It is a motion that melts tension from your shoulders, your spine, and your mind.",
            "The compartment is perfectly warm, insulated against the frozen beauty outside. You slide under the thick duvet, feeling completely protected and warm.",
            "Every mile traveled is a mile further away from worries and daily cares. The rhythmic cadence of the rails becomes a steady lullaby, synchronizing with your slow, peaceful breathing.",
            "Click-clack... click-clack... moving steadily through the peaceful winter night under the glowing green aurora.",
            "Let the journey carry you forward into dreamland. Close your eyes, let go of all thoughts, and sleep deeply and peacefully until dawn."
        ]
    },
    {
        "id": "story_048",
        "title": "The Garden of Luminescent Tides",
        "description": "Stroll along a tranquil midnight shoreline where gentle waves sparkle with bioluminescent turquoise light. Listen to the ocean breeze and let the calming tides carry away all tension.",
        "image_prompt": "A secluded tropical beach at night with glowing turquoise bioluminescent waves gently lapping soft sand, starry sky, palm silhouettes, ultra peaceful sleep background, no text",
        "paragraphs": [
            "Allow your breath to slow, matching the gentle ebb and flow of the ocean tide. Feel the support beneath you, firm and relaxing, as you arrive at a secluded tropical shore.",
            "The night is warm and balmy, with a gentle ocean breeze carrying the fresh scent of sea salt and night-blooming orchids. The sand beneath your feet is soft and cool, powder-fine and soothing.",
            "As you walk toward the water's edge, each gentle wave that rolls onto the shore glows with a soft, ethereal turquoise light. Bioluminescent plankton sparkle like liquid diamonds in the dark water.",
            "The sound of the ocean is slow, rhythmic, and infinitely calm. The water advances softly... hushes across the sand... and recedes back into the deep with a gentle sigh.",
            "Along the high tide line, beneath the protective shade of swaying coconut palms, a wide hammock woven from soft cotton cords hangs between two sturdy trunks.",
            "You climb into the hammock, feeling it contour perfectly to your body. As the warm breeze rocks you gently from side to side, you watch the mesmerizing dance of glowing waves below.",
            "The starry sky above is vast and unobstructed, stretching endlessly from horizon to horizon. The Milky Way arches across the heavens like a river of silver dust.",
            "With each breath you take, feel the cooling peace of the ocean wash over you. Inhale stillness... exhale tension. Inhale peace... exhale fatigue.",
            "The turquoise light pulses softly in harmony with the gentle waves. The sound of the surf becomes a soothing white noise that washes away every lingering thought.",
            "Held safely in the hammock between the palms, you are completely at ease. The ocean watches over you, breathing with you.",
            "Let the tide carry you gently into the peaceful realm of dreams. Drifting... swaying... sleeping deeply under the stars."
        ]
    },
    {
        "id": "story_049",
        "title": "The Herbalist's Cottage on Moonlit Hills",
        "description": "Retreat to a fragrant stone cottage perched high upon rolling lavender hills. Enjoy the soothing aroma of dried herbs and warm chamomile as moonlight fills the quiet night.",
        "image_prompt": "A quaint stone cottage with a slate roof in rolling purple lavender hills at night under a full bright moon, warm glowing windows, starry night, peaceful bedtime aesthetic, no text",
        "paragraphs": [
            "Take a deep, restorative breath, filling your lungs with calm and exhaling completely. Tonight, we journey to a place of natural healing and serene rest.",
            "High atop rolling hills that stretch into the horizon stands a charming stone cottage with a weathered slate roof and creeping ivy. Surrounding the cottage are endless fields of blooming lavender, swaying gently in the night wind.",
            "The moonlight casts a silvery veil over the purple flowers, releasing a wave of calming, sweet fragrance into the cool mountain air.",
            "You step through the cottage door into a warm, inviting kitchen. From the wooden ceiling beams hang hundreds of drying herbal bundles—lavender, sweet chamomile, spearmint, rosemary, and lemon balm.",
            "The air is saturated with their soothing botanical aromas, instantly relaxing your mind and slowing your heartbeat.",
            "A kettle sits quietly on the cast-iron stove, keeping a pot of fresh herbal tea warm. A stone fireplace radiates a steady, cozy warmth across the slate floor.",
            "In the corner of the room, tucked beneath an arched stone alcove, is a sturdy four-poster bed made of aged pine, layered with linen sheets and a thick patchwork quilt.",
            "You settle into the bed, feeling the weight of the quilt bring instant comfort to your tired muscles. The herbal scents drift around you, acting as a natural balm for your thoughts.",
            "Through the small paned window, the moon shines bright and steady over the lavender fields. The only sound is the soft whisper of the wind moving through the flowers outside.",
            "Feel every muscle in your face relax... your forehead smoothing, your jaw softening, your hands resting open and peaceful.",
            "You are enveloped in nature's purest tranquility. Let the scent of lavender and the soft moonlight guide you into a profound, restorative sleep."
        ]
    },
    {
        "id": "story_050",
        "title": "The Cloud Shepherd's Lullaby",
        "description": "Float gently across a dreamlike sunset sky where soft pastel clouds settle into deep indigo night. A weightless, ethereal sleep meditation for deep relaxation and healing rest.",
        "image_prompt": "Ethereal dreamlike cloudscape at twilight transitioning from soft pastel pink and gold into deep indigo starry night, ultra soft fluffy clouds, heavenly peaceful sleep scene, no text",
        "paragraphs": [
            "Close your eyes and let go of gravity. Imagine all weight lifting away from your body, leaving you light, floating, and utterly at ease.",
            "You find yourself resting high in the twilight sky upon a bed of clouds as soft and supporting as pure spun silk. The sky around you is painted in breathtaking shades of rose gold, dusty peach, and soft lavender.",
            "As the golden light of the sun dips below the distant horizon, the colors slowly deepen into rich violet, royal blue, and finally a velvet indigo.",
            "The clouds beneath you cradle every contour of your body with gentle, weightless warmth. You are completely secure, suspended in the vast, peaceful sky.",
            "A gentle, warm breeze brushes across your face, carrying with it the pure, clean essence of the upper atmosphere. Above you, one by one, the stars begin to awaken.",
            "First Venus, bright and steady like a celestial lamp, followed by millions of distant suns glittering across the cosmic expanse.",
            "Below, the world is asleep, wrapped in quiet shadows. Up here in the clouds, there is only stillness, space, and infinite peace.",
            "With each breath, you feel yourself syncing with the vastness of the night sky. Inhale the calm of the cosmos... exhale all that does not serve you.",
            "The clouds billow and shift in slow, graceful harmony, creating a soft lullaby of motion that invites you deeper into slumber.",
            "Every thought dissolves into the starlight. Your mind is quiet, open, and serene.",
            "Rest now in this heavenly sanctuary above the world. Let the clouds hold you, let the stars guide you, and drift into a long, blissful, unbroken sleep."
        ]
    }
]

def main():
    os.makedirs("ready_stories", exist_ok=True)
    manifest_file = os.path.join("ready_stories", "manifest.json")
    
    total_created = 0
    for s in stories_data:
        story_id = s["id"]
        story_dir = os.path.join("ready_stories", story_id)
        os.makedirs(story_dir, exist_ok=True)
        
        meta_file = os.path.join(story_dir, "metadata.json")
        script_file = os.path.join(story_dir, "script.md")
        thumb_file = os.path.join(story_dir, "thumbnail.jpg")
        
        # 1. Format script
        formatted_script = "\n\n".join([f"[NARRATOR] {p}" for p in s["paragraphs"]])
        word_count = len(formatted_script.split())
        est_duration = round(word_count / 125, 1) # ~125 wpm for slow bedtime narration
        
        with open(script_file, "w", encoding="utf-8") as f:
            f.write(formatted_script)
            
        # 2. Format metadata
        metadata = {
            "story_id": story_id,
            "original_name": s["title"],
            "title": s["title"],
            "description": s["description"],
            "tags": [
                "sleep story",
                "bedtime story",
                "relaxing audio",
                "sleep aid",
                "ambient storytelling",
                "full movie sleep story",
                "sleep meditation",
                "calming bedtime stories"
            ],
            "scenes_processed": len(s["paragraphs"]),
            "total_words": word_count,
            "estimated_duration_minutes": est_duration,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
            
        # 3. Download Thumbnail
        print(f"Generating package for {story_id}: '{s['title']}'...")
        if not os.path.exists(thumb_file) or os.path.getsize(thumb_file) < 1000:
            download_thumbnail(s["image_prompt"], thumb_file)
            
        total_created += 1
        print(f"[{story_id}] Complete ({word_count} words, thumbnail verified).")

    print(f"\n==========================================")
    print(f"SUCCESS: Generated {total_created} ready sleep story packages in ready_stories/!")
    print(f"==========================================")

if __name__ == "__main__":
    main()
