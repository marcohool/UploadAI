import json

dallePrompt = """```json
{
  "chosenLocation": "Manarola",
  "promptValue": "Create a hyper-realistic image capturing the twilight splendor of Manarola, one of the idyllic fishing villages of the Cinque Terre on the Italian Riviera. The composition should focus on the hillside with pastel-colored houses precariously clinging to the rugged cliffs. The image should be from a high vantage point looking down upon the village, enabling the viewer to feel as if they are gently gliding over it like a silent drone.

Include the following specific details:
- The charming, narrow streets winding through the clusters of buildings.
- Local villagers dressed in warm colors enjoying a relaxed evening, some savoring gelato, others chatting animatedly with expressive gestures.
- The fading golden sunlight spilling across the scene, reflecting off windows and casting the village in a warm, welcoming glow.
- The shimmering turquoise waters of the Mediterranean Sea gently lapping against the rocky shore, with small boats bobbing on the surface.
- Flower-filled balconies and patches of vibrant green vineyards contrast the earth-toned buildings.
- An array of ornate street lamps beginning to flicker on, offering a cozy, romantic ambience.

Desired Mood:
- Peaceful and serene with an enchanting ambiance, as if the village is a living painting from the Renaissance era.
- A sense of timeless beauty and a quiet, joyous life.

Perspective and Composition:
- Bird's-eye view with a slight tilt-shift effect to bring the center of the village into sharp focus while subtly blurring the edges.
- Ensure the entirety of the village is visible, with a backdrop of the dramatic coastline and twinkling horizon.

Lighting and Time of Day:
- Twilight, with the magic hour providing soft but radiant illumination to accentuate textures and natural colors.

Desired Action or Movement:
- A few seagulls soaring gracefully in the sky and the serene motion of the ocean.

Reflect the style of a postcard-perfect photograph that tempts viewers to step into the scene, instilling a lingering sense of wanderlust and admiration for the enduring allure of Italy.

Iterative Approach:
Start with a rough composition focusing on the light and placement of elements. Gradually refine the details and the interplay of colors, taking feedback on the lifelike qualities and emotional resonance of the scene with each iteration."
}
```
"""


dallePrompt = dallePrompt.strip('```json').replace("\n", "").replace("```", "")
print(dallePrompt)

jsonPrompt = json.loads(dallePrompt)
