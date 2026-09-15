#pragma once

#include <NEMain.h>

#include "math/Vec2.h"

// Polygon ID ranges. Outlines are drawn where IDs differ, and the outline
// colour slot is id >> 3, so every group owns 8 IDs sharing one colour slot.
enum class PolyGroup : u32
{
    Ground = 0,
    Forest = 8,
    Nina = 16,
    Mats = 24,
    Mushrooms = 32,
    Effects = 40,
    Shroomchen = 48,
};

enum class Lighting
{
    Lit,         // sun / moon light, follows the time of day
    LitTwoSided, // lit, no back-face culling (thin gills in the inspection view)
    Glow,        // unlit, full brightness, double-sided (needs an emissive material)
};

// A light that only reaches nearby objects (the lantern). The DS has no point
// lights, so light 1 is re-aimed and dimmed for every object before it is drawn.
struct PointLight
{
    Vec2 position;
    Fixed radius;
    u32 color;
};

// Lighting mood of the scene, see TimeOfDayService.
struct Atmosphere
{
    u32 sky;     // clear colour and fog colour
    u32 light;   // sun / moon colour
    u32 ambient; // material ambient
    u32 outline;
    s32 lightX, lightY, lightZ; // light direction (v10)
    s32 fogDepth;               // where the fog starts (0 - 0x7FFF, lower = closer)
    s32 shadowLength;           // shadow length per unit of height (20.12 raw)
    s32 shadowAlpha;            // 0 = no shadows, up to 31
};

// Light distance haze instead of the forest fog (the final picture): its own
// colour, and it never fully covers what is behind it.
struct Haze
{
    u32 color;
    s32 depth;       // where the haze starts (0 - 0x7FFF)
    u32 shift;       // width of the fog bands (bigger = shorter ramp)
    u32 maxDensity;  // strength at the end of the ramp (0 - 127)
};

// Owns the Nitro Engine setup: screen effects, lights, fog and the frame dispatch.
class RenderService
{
public:
    void Init();

    // Materials whose ambient colour follows the atmosphere.
    void AddLitMaterial(NE_Material *material);
    void ApplyAtmosphere(const Atmosphere &atmosphere);

    // Effective fog start; setting it keeps an offset to the atmosphere (debug tuning).
    void SetFogDepth(int depth);
    int FogDepth() const;
    // Fog is on in the forest and off in the inspection view.
    void SetFogEnabled(bool enabled);
    // Forces a fog start (e.g. while Shroomchen lights up the forest); -1 = off.
    void SetFogOverride(int depth);
    // Replaces the fog with a haze; nullptr goes back to the normal fog.
    void SetHaze(const Haze *haze);
    // Far clipping plane (the forest uses kDefaultViewDistance).
    static constexpr Fixed kDefaultViewDistance = 32_fx;
    // Nitro Engine's field of view after NE_Init3D (the forest camera).
    static constexpr int kDefaultFieldOfView = 70;
    void SetViewDistance(Fixed distance);

    // Sets the polygon format for following draws: fogged, back-face culled.
    void BeginPolygons(PolyGroup group, u32 index = 0, Lighting lighting = Lighting::Lit) const;
    // Translucent, unlit polygons (alpha 1-30), e.g. the lantern's light pool.
    void BeginTranslucent(PolyGroup group, u32 index, u32 alpha) const;

    // Point light for the following objects; nullptr switches it off.
    void SetPointLight(const PointLight *light) { pointLight_ = light; }
    // Aims the point light at an object about to be drawn (call inside Draw3D).
    void LightObject(Vec2 position) const;
    // For large objects like the ground that the point light must not tint.
    void ClearObjectLight() const;

    // Shadows of the current atmosphere (see ShadowCaster).
    Fixed ShadowLength() const { return Fixed::FromRaw(atmosphere_.shadowLength); }
    u32 ShadowAlpha() const { return static_cast<u32>(atmosphere_.shadowAlpha); }
    // Direction shadows fall on the ground (the sun light's horizontal direction).
    Vec2 SunDirection() const;

    // 2D overlay helper; call NE_2DViewInit() and set a polygon format first.
    // Draws the texture rectangle (u, v, uw, vh) at the screen rectangle (x, y, w, h).
    static void Draw2DImage(const NE_Material *material, int x, int y, int w, int h,
                            int u, int v, int uw, int vh, s16 depth, u32 color);

    // Renders one frame; calls scene.Draw3D() inside the engine's frame.
    template <typename Scene>
    void Render(Scene &scene)
    {
        struct Frame
        {
            RenderService *self;
            Scene *scene;
        };
        Frame frame = { this, &scene };

        NE_ProcessArg(
            [](void *arg) {
                Frame *f = static_cast<Frame *>(arg);
                f->scene->Draw3D();
                // The counters are reset by the buffer swap, so they must be
                // sampled here, right before the engine flushes the frame.
                f->self->polygonCount_ = NE_GetPolygonCount();
                f->self->vertexCount_ = NE_GetVertexCount();
            },
            &frame);
    }

    // Polygons / vertices of the last rendered frame (limits 2048 / 6144).
    int PolygonCount() const { return polygonCount_; }
    int VertexCount() const { return vertexCount_; }

private:
    void ApplyFog();

    static constexpr int kMaxLitMaterials = 4;

    NE_Material *litMaterials_[kMaxLitMaterials] = {};
    int litMaterialCount_ = 0;
    Atmosphere atmosphere_ = {};
    int fogOffset_ = 0;
    bool fogEnabled_ = true;
    int fogOverride_ = -1;
    const Haze *haze_ = nullptr;
    const PointLight *pointLight_ = nullptr;
    int polygonCount_ = 0;
    int vertexCount_ = 0;
};
