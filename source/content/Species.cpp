#include "content/Species.h"

namespace {

// Same order as SpeciesId. Facts: see the Pilzbuch table in the plan (BfR, Wikipedia DE).
// 14 mushrooms grow in the forest; the forest-god mushroom is placed by the story.
constexpr SpeciesInfo kSpecies[] = {
    { "Steinpilz", Edibility::Edible, Habitat::Ground,
      ModelId::Steinpilz, ModelId::DetailSteinpilz, 2,
      "essbar" },
    { "Satans-Röhrling", Edibility::Poisonous, Habitat::Ground,
      ModelId::SatansRoehrling, ModelId::DetailSatansRoehrling, 2,
      "giftig" },
    { "Wiesen-Champignon", Edibility::Edible, Habitat::Ground,
      ModelId::Champignon, ModelId::DetailChampignon, 2,
      "essbar" },
    { "Grüner Knollenblätterpilz", Edibility::DeadlyPoisonous, Habitat::Ground,
      ModelId::Knollenblaetterpilz, ModelId::DetailKnollenblaetterpilz, 2,
      "tödlich giftig" },
    { "Echter Pfifferling", Edibility::Edible, Habitat::Ground,
      ModelId::Pfifferling, ModelId::DetailPfifferling, 2,
      "essbar" },
    { "Fliegenpilz", Edibility::Poisonous, Habitat::Ground,
      ModelId::Fliegenpilz, ModelId::DetailFliegenpilz, 2,
      "giftig" },
    { "Ölbaum-Trichterling", Edibility::DeadlyPoisonous, Habitat::Wood,
      ModelId::OelbaumTrichterling, ModelId::DetailOelbaumTrichterling, 2,
      "sehr giftig" },
    { "Waldgott-Pilz", Edibility::Magic, Habitat::Shrine,
      ModelId::WaldgottPilz, ModelId::DetailWaldgottPilz, 0,
      "???" },
};

} // namespace

const SpeciesInfo &Species(SpeciesId id)
{
    static_assert(sizeof(kSpecies) / sizeof(kSpecies[0]) == static_cast<size_t>(SpeciesId::Count),
                  "kSpecies must list every SpeciesId");
    return kSpecies[static_cast<size_t>(id)];
}
