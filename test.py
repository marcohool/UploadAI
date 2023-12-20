dallePrompt = """```json
{
  "chosenLocation": "Budapest",
  "promptValue": "Create a hyper-realistic, dynamic image of Budapest that captures the essence of the city merging past and present. Center the composition on the iconic Chain Bridge (Széchenyi Lánchíd) over the Danube, with the imposing Buda Castle in the background, basked in the warm golden glow of the setting sun. The color palette should consist of rich oranges and pinks reflecting off the clouds, contrasting with the deep blues of the twilight sky and river waters. Incorporate the intricate architectural details of the bridge, the gothic elements of the castle, and add the vivid green of the Buda hills. The mood should be peaceful yet awe-inspiring, capturing a moment of serene beauty amid the city’s bustling life. Include a few small boats gliding on the river, their wooden hulls adding a sense of gentle motion. The perspective should be from the Pest side of the river looking towards Buda, slightly elevated, as if taken from the parapet of the Parliament building. The focus should be razor-sharp, with soft, realistic lighting enhancing textures and surfaces. For additional refinement, after an initial draft, adjustments may include emphasizing the reflection of the city lights on the water, increasing the contrast between shadows and highlighted areas, and possibly introducing a faint mist to accentuate the fairy-tale ambiance. The overall style should bridge classical romanticism with modern photographic clarity, resulting in an art piece that would not look out of place on the cover of a luxury travel magazine."
}
```"""


dallePromptJson = dallePrompt.replace(
    "```json\n", "").replace("\n```", "").strip()
print("Dalle prompt to JSON -> ", dallePromptJson)
