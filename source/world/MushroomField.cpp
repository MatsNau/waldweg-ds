#include "world/MushroomField.h"

#include "core/Random.h"
#include "render/AssetService.h"
#include "render/RenderService.h"
#include "world/Forest.h"

namespace {

// Mushrooms keep this distance to trees and props, so the camera can see them
// and Nina can walk up to them.
constexpr Fixed kClearance = 1.0_fx;
constexpr Fixed kMinSpacing = 2.2_fx;
constexpr Fixed kStumpTop = 0.45_fx;
// The forest-god mushroom keeps some distance to the shrine and the start.
constexpr Fixed kGodAwayFromShrine = 4_fx;
constexpr Fixed kGodAwayFromSpawn = 5_fx;

// Same culling window as the forest.
constexpr Fixed kCullAhead = 11_fx;
constexpr Fixed kCullBehind = 3.5_fx;
constexpr Fixed kCullHalfWidth = 12_fx;

} // namespace

void MushroomField::Generate(const Forest &forest, u32 seed, u32 godSeed)
{
    Random random(seed);
    count_ = 0;
    // Count every mushroom (also the hidden god mushroom) when spacing them.
    godVisible_ = true;

    // Stumps first: every wood species gets its own stump.
    int stumpCursor = 0;

    for (int s = 0; s < static_cast<int>(SpeciesId::Count); s++)
    {
        const SpeciesInfo &info = Species(static_cast<SpeciesId>(s));
        for (int n = 0; n < info.worldCount; n++)
        {
            SpeciesId species = static_cast<SpeciesId>(s);
            int rotation = random.Range(0, 511);

            if (info.habitat == Habitat::Wood)
            {
                for (; stumpCursor < forest.PropCount(); stumpCursor++)
                {
                    const Prop &prop = forest.PropAt(stumpCursor);
                    if (prop.kind == PropKind::Stump)
                    {
                        Add(prop.position, kStumpTop, species, rotation);
                        stumpCursor++;
                        break;
                    }
                }
                continue;
            }

            // Ground species: free spot, not too close to other mushrooms.
            for (int attempt = 0; attempt < 40; attempt++)
            {
                Vec2 spot;
                if (!forest.FindFreeSpot(random, kClearance, spot))
                    break;
                if (FindNear(spot, kMinSpacing) >= 0)
                    continue;
                Add(spot, 0_fx, species, rotation);
                break;
            }
        }
    }

    // The forest-god mushroom: somewhere else in every game.
    Random godRandom(godSeed);
    for (int attempt = 0; attempt < 200; attempt++)
    {
        Vec2 spot;
        if (!forest.FindFreeSpot(godRandom, kClearance, spot))
            continue;
        Fixed toShrine = (spot - forest.ShrinePosition()).LengthSq();
        Fixed toSpawn = (spot - forest.SpawnPoint()).LengthSq();
        if (toShrine < kGodAwayFromShrine * kGodAwayFromShrine || toSpawn < kGodAwayFromSpawn * kGodAwayFromSpawn ||
            FindNear(spot, kMinSpacing) >= 0)
            continue;
        Add(spot, 0_fx, SpeciesId::WaldgottPilz, 0);
        break;
    }
    godVisible_ = false;
}

bool MushroomField::Add(Vec2 position, Fixed height, SpeciesId species, int rotation)
{
    if (count_ >= kMaxMushrooms)
        return false;
    mushrooms_[count_++] = { position, height, species, rotation, true };
    return true;
}

int MushroomField::RemainingCount() const
{
    int remaining = 0;
    for (int i = 0; i < count_; i++)
    {
        if (mushrooms_[i].present)
            remaining++;
    }
    return remaining;
}

bool MushroomField::Hidden(const Mushroom &m) const
{
    return !m.present || (m.species == SpeciesId::WaldgottPilz && !godVisible_);
}

bool MushroomField::IsVisible(int index) const
{
    return !Hidden(mushrooms_[index]);
}

bool MushroomField::IsInReach(int index, Vec2 nina) const
{
    const Mushroom &m = mushrooms_[index];
    return !Hidden(m) && (m.position - nina).LengthSq() <= kReach * kReach;
}

int MushroomField::FindNear(Vec2 position, Fixed radius) const
{
    int best = -1;
    Fixed bestDistanceSq = radius * radius;
    for (int i = 0; i < count_; i++)
    {
        if (Hidden(mushrooms_[i]))
            continue;
        Fixed distanceSq = (mushrooms_[i].position - position).LengthSq();
        if (distanceSq <= bestDistanceSq)
        {
            best = i;
            bestDistanceSq = distanceSq;
        }
    }
    return best;
}

void MushroomField::Draw(const RenderService &render, Vec2 cameraFocus) const
{
    for (int i = 0; i < count_; i++)
    {
        const Mushroom &m = mushrooms_[i];
        if (Hidden(m))
            continue;

        Fixed ahead = cameraFocus.z - m.position.z;
        if (ahead > kCullAhead || ahead < -kCullBehind ||
            fx::Abs(m.position.x - cameraFocus.x) > kCullHalfWidth)
            continue;

        ModelId modelId = Species(m.species).worldModel;
        NE_Model *model = assets_.Model(modelId);
        NE_ModelSetCoordI(model, m.position.x.Raw(), m.height.Raw(), m.position.z.Raw());
        NE_ModelSetRot(model, 0, m.rotation, 0);
        render.LightObject(m.position);
        render.BeginPolygons(PolyGroup::Mushrooms, static_cast<u32>(i),
                             AssetService::IsGlowing(modelId) ? Lighting::Glow : Lighting::Lit);
        NE_ModelDraw(model);
    }
}
