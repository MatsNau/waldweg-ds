#include "render/AssetService.h"

#include "core/Fatal.h"

namespace {

// Same order as ModelId.
constexpr const char *kModelPaths[] = {
    "models/ground.bin",
    "models/tree_round.bin",
    "models/tree_golden.bin",
    "models/tree_fir.bin",
    "models/bush.bin",
    "models/rock.bin",
    "models/stump.bin",
    "models/shrine.bin",
    "models/shadow.bin",
    "models/leaf_a.bin",
    "models/leaf_b.bin",
    "models/leaf_c.bin",
    "models/nina_head.bin",
    "models/nina_body.bin",
    "models/nina_arm.bin",
    "models/nina_leg.bin",
    "models/mats_head.bin",
    "models/mats_body.bin",
    "models/mats_arm.bin",
    "models/mats_leg.bin",
    "models/pilz_steinpilz.bin",
    "models/pilz_satansroehrling.bin",
    "models/pilz_champignon.bin",
    "models/pilz_knollenblaetterpilz.bin",
    "models/pilz_pfifferling.bin",
    "models/pilz_fliegenpilz.bin",
    "models/pilz_oelbaum_trichterling.bin",
    "models/pilz_waldgott.bin",
    "models/item_korb.bin",
    "models/item_schal.bin",
    "models/item_laterne.bin",
    "models/item_laterne_glas.bin",
    "models/item_gloeckchen.bin",
    "models/licht_scheibe.bin",
    "models/item_muetze.bin",
    "models/detail_steinpilz.bin",
    "models/detail_satansroehrling.bin",
    "models/detail_champignon.bin",
    "models/detail_knollenblaetterpilz.bin",
    "models/detail_pfifferling.bin",
    "models/detail_fliegenpilz.bin",
    "models/detail_oelbaum_trichterling.bin",
    "models/detail_waldgott.bin",
    "models/cow_body.bin",
    "models/cow_leg.bin",
    "models/cow_crown.bin",
    "models/end_hill.bin",
};

constexpr const char *kPalettePath = "textures/palette.grf";

} // namespace

bool AssetService::IsGlowing(ModelId id)
{
    return id == ModelId::LanternGlass || id == ModelId::LightDisc || id == ModelId::WaldgottPilz ||
           id == ModelId::Shadow ||
           id == ModelId::DetailWaldgottPilz;
}

ModelId AssetService::GlowPartOf(ModelId id)
{
    return id == ModelId::Lantern ? ModelId::LanternGlass : ModelId::Count;
}

void AssetService::LoadAll()
{
    static_assert(sizeof(kModelPaths) / sizeof(kModelPaths[0]) == static_cast<size_t>(ModelId::Count),
                  "kModelPaths must list every ModelId");

    palette_ = NE_MaterialCreate();
    if (NE_MaterialTexLoadGRF(palette_, nullptr, NE_TEXGEN_TEXCOORD, kPalettePath) == 0)
        Fatal("Textur fehlt:\n%s", kPalettePath);

    // Unlit polygons only get emission, so the texture shows at full brightness
    // regardless of the time of day.
    glow_ = NE_MaterialCreate();
    NE_MaterialClone(palette_, glow_);
    NE_MaterialSetProperties(glow_, RGB15(0, 0, 0), RGB15(0, 0, 0), RGB15(0, 0, 0),
                             RGB15(31, 31, 31), false, false);

    for (size_t i = 0; i < models_.size(); i++)
    {
        NE_Model *model = NE_ModelCreate(NE_Static);
        if (NE_ModelLoadStaticMeshFAT(model, kModelPaths[i]) == 0)
            Fatal("Modell fehlt:\n%s", kModelPaths[i]);
        NE_ModelSetMaterial(model, IsGlowing(static_cast<ModelId>(i)) ? glow_ : palette_);
        models_[i] = model;
    }
}
