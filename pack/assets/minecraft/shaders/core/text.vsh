#version 330
#extension GL_ARB_separate_shader_objects : require

#if !defined(IS_GUI) && !defined(IS_SEE_THROUGH)
#include <minecraft:fog.glsl>
#include <minecraft:sample_lightmap.glsl>
#endif

#include <minecraft:dynamictransforms.glsl>
#include <minecraft:projection.glsl>

layout(location = 0) in vec3 Position;
layout(location = 1) in vec4 Color;
layout(location = 2) in vec2 UV0;
#if !defined(IS_GUI) && !defined(IS_SEE_THROUGH)
layout(location = 3) in ivec2 UV2;
#endif

#if !defined(IS_GUI) && !defined(IS_SEE_THROUGH)
uniform sampler2D Sampler2;
layout(location = 0) out float sphericalVertexDistance;
layout(location = 1) out float cylindricalVertexDistance;
#endif

layout(location = 2) out vec4 vertexColor;
layout(location = 3) out vec2 texCoord0;

#ifdef IS_GUI
// lairner Defusal kill feed: vanilla text.vsh plus this block and the two marked lines in main().
// The server draws the feed as a boss bar title whose right edge is FEED_X GUI px right of the screen
// center. Glyphs in the reserved colors below (main text) or the reserved shadow (alpha 254) are moved so
// the right edge ends FEED_MARGIN GUI px left of the real right screen edge, at any GUI scale and window
// size. FEED_X must equal the server's config feed-x. Anything else is drawn as in vanilla.
const float FEED_X = 200.0;
const float FEED_MARGIN = 4.0;

bool feed_marked(vec4 c) {
    ivec4 b = ivec4(floor(c * 255.0 + 0.5));
    if (b.a == 255) {
        return b.rgb == ivec3(254, 254, 253)    // white
            || b.rgb == ivec3(255, 170, 1)      // T (gold)
            || b.rgb == ivec3(85, 255, 254);    // CT (aqua)
    }
    return b == ivec4(14, 15, 16, 254);         // shadow of the marked text
}

float feed_shift() {
    float guiWidth = 2.0 / ProjMat[0][0];       // ortho projection: m00 = 2 / width in GUI px
    return guiWidth * 0.5 - FEED_X - FEED_MARGIN;
}
#endif

void main() {
    vec3 pos = Position;
#ifdef IS_GUI
    if (feed_marked(Color)) {
        pos.x += feed_shift();
    }
#endif
    gl_Position = ProjMat * ModelViewMat * vec4(pos, 1.0);

#if !defined(IS_GUI) && !defined(IS_SEE_THROUGH)
    sphericalVertexDistance = fog_spherical_distance(Position);
    cylindricalVertexDistance = fog_cylindrical_distance(Position);
    vertexColor = Color * sample_lightmap(Sampler2, UV2);
#else
    vertexColor = Color;
#endif
    texCoord0 = UV0;
}
