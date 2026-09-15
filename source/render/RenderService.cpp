#include "render/RenderService.h"

#include "core/Fatal.h"

namespace {

// Fog reaches full strength 512 depth units after its start (~22 units away at day).
constexpr u32 kFogShift = 4;
constexpr int kFogMass = 2;
constexpr Fixed kNearPlane = 0.25_fx;
constexpr int kFogBands = 32;
constexpr u32 kOutlineSlots = 8;
constexpr int kPointLightIndex = 1;

// v10 (1.0 = 512) from 20.12 fixed point, clamped to the valid range.
s32 ToV10(Fixed value)
{
    s32 v = value.Raw() >> 3;
    if (v > 511)
        return 511;
    if (v < -512)
        return -512;
    return v;
}

u32 ScaleColor(u32 color, Fixed level)
{
    s32 r = ((color & 31) * level.Raw()) >> Fixed::kShift;
    s32 g = (((color >> 5) & 31) * level.Raw()) >> Fixed::kShift;
    s32 b = (((color >> 10) & 31) * level.Raw()) >> Fixed::kShift;
    return RGB15(r, g, b);
}

} // namespace

void RenderService::Init()
{
    if (NE_Init3D() != 0)
        Fatal("Nitro Engine konnte nicht starten.");

    // NFLib uses VRAM C/D for the sub screen, so textures may only use A/B.
    // (TopTextService uses VRAM F for the dialog text on the top screen.)
    NE_TextureSystemReset(0, 0, NE_VRAM_AB);

    SetViewDistance(kDefaultViewDistance);
    NE_FogEnableBackground(true);
    NE_OutliningEnable(true);
}

void RenderService::AddLitMaterial(NE_Material *material)
{
    if (litMaterialCount_ >= kMaxLitMaterials)
        Fatal("Zu viele beleuchtete Materialien.");
    litMaterials_[litMaterialCount_++] = material;
}

void RenderService::ApplyAtmosphere(const Atmosphere &atmosphere)
{
    atmosphere_ = atmosphere;

    NE_ClearColorSet(atmosphere.sky, 31, 63);
    NE_LightSetI(0, atmosphere.light, atmosphere.lightX, atmosphere.lightY, atmosphere.lightZ);
    for (int i = 0; i < litMaterialCount_; i++)
    {
        NE_MaterialSetProperties(litMaterials_[i],
                                 RGB15(31, 31, 31), atmosphere.ambient,
                                 RGB15(0, 0, 0), RGB15(0, 0, 0),
                                 false, false);
    }
    for (u32 i = 0; i < kOutlineSlots; i++)
        NE_OutliningSetColor(i, atmosphere.outline);

    ApplyFog();
}

void RenderService::SetFogOverride(int depth)
{
    fogOverride_ = depth;
    ApplyFog();
}

int RenderService::FogDepth() const
{
    int depth = fogOverride_ >= 0 ? fogOverride_ : atmosphere_.fogDepth + fogOffset_;
    if (depth < 0x7000)
        return 0x7000;
    if (depth > 0x7FFF)
        return 0x7FFF;
    return depth;
}

void RenderService::SetFogDepth(int depth)
{
    fogOffset_ = depth - atmosphere_.fogDepth;
    ApplyFog();
}

void RenderService::SetFogEnabled(bool enabled)
{
    fogEnabled_ = enabled;
    ApplyFog();
}

void RenderService::SetHaze(const Haze *haze)
{
    haze_ = haze;
    ApplyFog();
}

void RenderService::SetViewDistance(Fixed distance)
{
    NE_ClippingPlanesSetI(kNearPlane.Raw(), distance.Raw());
}

void RenderService::ApplyFog()
{
    if (!fogEnabled_)
    {
        NE_FogDisable();
    }
    else if (haze_ != nullptr)
    {
        NE_FogEnable(haze_->shift, haze_->color, 31, kFogMass, haze_->depth);
        // The haze is for far geometry; the clear colour stays as it is.
        NE_FogEnableBackground(false);
        // Linear ramp that stops at maxDensity instead of covering everything.
        for (int i = 0; i < kFogBands; i++)
            GFX_FOG_TABLE[i] = static_cast<u8>(haze_->maxDensity * i / (kFogBands - 1));
    }
    else
    {
        NE_FogEnable(kFogShift, atmosphere_.sky, 31, kFogMass, FogDepth());
        NE_FogEnableBackground(true);
    }
}

void RenderService::Draw2DImage(const NE_Material *material, int x, int y, int w, int h,
                                int u, int v, int uw, int vh, s16 depth, u32 color)
{
    NE_MaterialUse(material);
    GFX_COLOR = color;
    GFX_BEGIN = GL_QUADS;

    int x2 = x + w;
    int y2 = y + h;
    GFX_TEX_COORD = TEXTURE_PACK(inttot16(u), inttot16(v));
    GFX_VERTEX16 = (y << 16) | (x & 0xFFFF);
    GFX_VERTEX16 = static_cast<u16>(depth);

    GFX_TEX_COORD = TEXTURE_PACK(inttot16(u), inttot16(v + vh));
    GFX_VERTEX_XY = (y2 << 16) | (x & 0xFFFF);

    GFX_TEX_COORD = TEXTURE_PACK(inttot16(u + uw), inttot16(v + vh));
    GFX_VERTEX_XY = (y2 << 16) | (x2 & 0xFFFF);

    GFX_TEX_COORD = TEXTURE_PACK(inttot16(u + uw), inttot16(v));
    GFX_VERTEX_XY = (y << 16) | (x2 & 0xFFFF);
}

void RenderService::BeginPolygons(PolyGroup group, u32 index, Lighting lighting) const
{
    u32 id = static_cast<u32>(group) + (index % 8);
    bool lit = lighting != Lighting::Glow;
    bool culled = lighting == Lighting::Lit;
    NE_PolyFormat(31, id, lit ? NE_LIGHT_01 : static_cast<NE_LightEnum>(0),
                  culled ? NE_CULL_BACK : NE_CULL_NONE, static_cast<NE_OtherFormatEnum>(NE_FOG_ENABLE));
}

void RenderService::BeginTranslucent(PolyGroup group, u32 index, u32 alpha) const
{
    u32 id = static_cast<u32>(group) + (index % 8);
    NE_PolyFormat(alpha, id, static_cast<NE_LightEnum>(0), NE_CULL_NONE,
                  static_cast<NE_OtherFormatEnum>(NE_FOG_ENABLE));
}

Vec2 RenderService::SunDirection() const
{
    Vec2 direction = { Fixed::FromRaw(atmosphere_.lightX << 3), Fixed::FromRaw(atmosphere_.lightZ << 3) };
    Vec2 normalized = direction.Normalized();
    return normalized.IsZero() ? Vec2{ 0_fx, -1_fx } : normalized;
}

void RenderService::ClearObjectLight() const
{
    NE_LightSetI(kPointLightIndex, 0, 0, -511, 0);
}

void RenderService::LightObject(Vec2 position) const
{
    if (pointLight_ == nullptr)
    {
        ClearObjectLight();
        return;
    }

    Vec2 away = position - pointLight_->position;
    Fixed distance = away.Length();
    if (distance >= pointLight_->radius)
    {
        ClearObjectLight();
        return;
    }

    Fixed level = 1_fx - distance / pointLight_->radius;
    level = level * level; // softer falloff towards the edge

    // Light travels from the lantern to the object, a bit downwards and away
    // from the camera, so the sides facing the lantern and the camera light up.
    Vec2 dir = distance > 0.1_fx ? away * (1_fx / distance) : Vec2{};
    NE_LightSetI(kPointLightIndex, ScaleColor(pointLight_->color, level),
                 ToV10(dir.x * 0.7_fx), ToV10(-0.55_fx), ToV10(dir.z * 0.7_fx - 0.45_fx));
}
