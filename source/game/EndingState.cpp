#include "game/EndingState.h"

#include <stdio.h>

#include "content/Ending.h"
#include "core/Fatal.h"
#include "core/InputService.h"
#include "render/RenderService.h"
#include "ui/SubScreenService.h"
#include "ui/TextService.h"
#include "ui/UiLayout.h"

namespace {

// Olive green of the valley at the bottom edge of the upper picture: the clear
// colour behind the hill, so the two screens meet without a seam.
constexpr u32 kMeadow = RGB15(12, 12, 6);

// Warm sunrise light coming from the sun ahead (towards the camera).
const Atmosphere kSunrise = {
    kMeadow, RGB15(31, 27, 20), RGB15(20, 18, 15), RGB15(8, 5, 3),
    floattov10(0.2), floattov10(-0.8), floattov10(0.55), 0x7D40, 0, 0,
};

// Soft morning haze: far trees fade towards the valley colours of the upper
// picture, but stay visible. The camera looks ~35 units far.
const Haze kMorningHaze = { RGB15(19, 19, 12), 0x7CC0, 5, 72 };
constexpr Fixed kViewDistance = 64_fx;

constexpr Fixed kHillScale = 3.5_fx;

// The three sit on the hilltop, just before the crest.
constexpr Fixed kSeatZ = 1.9_fx;

// Height of the hill (same shape as make_hill in assets/blender/models_ending.py).
constexpr Fixed kCrestZ = 1.2_fx;
constexpr Fixed kSteepness = 0.16_fx;
constexpr Fixed kValleyFloor = -9_fx;
constexpr Fixed kOppositeZ = -12_fx;
constexpr Fixed kOppositeRise = 0.1_fx;
constexpr Fixed kOppositeTop = 7_fx;
constexpr Fixed kOppositeRiseMax = 14_fx;

Fixed HillHeight(Fixed x, Fixed z)
{
    // Clamp before squaring, so far values can't overflow.
    Fixed drop = fx::Min(fx::Max(kCrestZ - z, 0_fx), 8_fx);
    Fixed height = fx::Max(-(drop * drop * kSteepness) - (x * x * 0.003_fx), kValleyFloor);
    Fixed rise = fx::Min(fx::Max(kOppositeZ - z, 0_fx), kOppositeRiseMax);
    return fx::Min(height + rise * rise * kOppositeRise, kOppositeTop);
}

// Forest cards: the texture holds four 32x32 trees.
constexpr const char *kTreeCardsPath = "textures/treecards.grf";
constexpr u32 kCardPolygonId = 9;
constexpr int kFieldOfView = 50;
constexpr u32 kCardTint = RGB15(31, 27, 22); // warm morning light
// The hill is unlit like the cards: lit against the sun it would turn almost black.
constexpr u32 kHillTint = RGB15(29, 31, 24);

constexpr int kFadeFrames = 120;
// Dialog timeline (frames after entering).
constexpr int kFirstLineFrame = 200;
constexpr int kLineFrames = 270;
// After the last line the picture stays until a button is pressed, then a new game starts.
constexpr int kLeaveFadeFrames = 90;

constexpr int kPuffCycle = 160;
constexpr int kPuffRise = 30;
constexpr int kPuffDrift = 8;

} // namespace

EndingState::EndingState(Services &services, StateMachine &machine)
    : services_(services), machine_(machine), cow_(services.assets), nina_(services.assets), mats_(services.assets),
      leaves_(services.assets, 0xAB12)
{
}

void EndingState::Init()
{
    camera_ = NE_CameraCreate();
    if (camera_ == nullptr)
        Fatal("Kamera konnte nicht erstellt werden.");
    // Behind the three, looking over the hill towards the village.
    // Looking down onto the meadow, so it fills the lower screen.
    // Low behind the three: they sit big at the bottom, the forest fills the rest.
    NE_CameraSetI(camera_, floattof32(0.1), floattof32(2.3), floattof32(6.2),
                  floattof32(0.1), floattof32(-1.0), floattof32(-10.0), 0, Fixed::kOne, 0);

    treeCards_ = NE_MaterialCreate();
    if (NE_MaterialTexLoadGRF(treeCards_, nullptr, NE_TEXGEN_TEXCOORD, kTreeCardsPath) == 0)
        Fatal("Textur fehlt:\n%s", kTreeCardsPath);
    PlantForest();

    hillMaterial_ = NE_MaterialCreate();
    NE_MaterialClone(services_.assets.PaletteMaterial(), hillMaterial_);
    NE_MaterialSetProperties(hillMaterial_, RGB15(0, 0, 0), RGB15(0, 0, 0), RGB15(0, 0, 0), kHillTint, false, false);
    NE_ModelSetMaterial(services_.assets.Model(ModelId::EndHill), hillMaterial_);
}

void EndingState::LoadChimneys()
{
    chimneyCount_ = 0;
    FILE *file = fopen("book/ending_chimneys.txt", "r");
    if (file == nullptr)
        return;
    int x = 0;
    int y = 0;
    while (chimneyCount_ < kMaxChimneys && fscanf(file, "%d %d", &x, &y) == 2)
        chimneys_[chimneyCount_++] = { x, y };
    fclose(file);
}

void EndingState::Enter()
{
    fader_.SetBlack();
    fader_.FadeIn(kFadeFrames);
    frame_ = 0;
    nextStep_ = 0;
    leaving_ = false;

    // The 3D picture goes to the lower screen, the drawn sky to the upper one.
    NE_MainScreenSetOnBottom();
    NE_SetFov(kFieldOfView);
    RenderService &render = services_.render;
    render.SetFogEnabled(true);
    render.SetFogOverride(-1);
    render.SetPointLight(nullptr);
    render.ApplyAtmosphere(kSunrise);
    render.SetViewDistance(kViewDistance);
    render.SetHaze(&kMorningHaze);

    SubScreenService &sub = services_.subScreen;
    sub.EnterEndingMode();
    services_.text.Clear();
    services_.text.Present();

    LoadChimneys();
    if (!spritesCreated_)
    {
        for (int i = 0; i < chimneyCount_ * kPuffsPerChimney; i++)
            puffSprites_[i] = sub.CreateSprite(ui::Sheet::Icons, ui::kIconSmokeSmall, 0, 0, 2);
        for (int i = 0; i < kSkyLeaves; i++)
            skyLeafSprites_[i] = sub.CreateSprite(ui::Sheet::Icons, ui::kIconSmallLeaf, 0, 0, 2);
        spritesCreated_ = true;
    }
    for (SkyLeaf &leaf : skyLeaves_)
        ResetSkyLeaf(leaf, true);
    leaves_.Clear();

    // All three sit side by side with their backs to the camera.
    Angle away = Angle::FromDegrees(180);
    nina_.Place({ -0.75_fx, kSeatZ }, away);
    nina_.SetSitting(true);
    nina_.SetWearingHat(true);
    mats_.Place({ 0.05_fx, kSeatZ + 0.05_fx }, away);
    mats_.SetSitting(true);
    mats_.ShowItem(ItemId::Scarf);

    cow_.Place({ 1.25_fx, kSeatZ - 0.2_fx }, away);
    cow_.SetScale(1.1_fx);
    cow_.SetDeity(false);
    cow_.SetLying(true);
    cow_.SetWreath(true);
    cow_.SetVisible(true);
}

void EndingState::Exit()
{
    RenderService &render = services_.render;
    render.SetHaze(nullptr);
    render.SetViewDistance(RenderService::kDefaultViewDistance);
    NE_SetFov(RenderService::kDefaultFieldOfView);
    NE_MainScreenSetOnTop();

    HideDialog();
    services_.subScreen.ExitEndingMode();
    leaves_.Clear();
}

void EndingState::ShowLine(int index)
{
    TextService &text = services_.text;
    const ending::Line &line = ending::kDialog[index];

    services_.subScreen.ShowDialogPanel(true);
    text.Clear();
    text.SetColor(TextColor::Speaker);
    text.Format(ui::kPanelColumn, ui::kPanelRow, "%s:", line.speaker);
    text.SetColor(TextColor::Ink);
    text.WriteWrapped(ui::kPanelColumn, ui::kPanelRow + 1, ui::kPanelColumns, ui::kPanelRows - 1, line.text);
    text.Present();
}

void EndingState::HideDialog()
{
    services_.subScreen.ShowDialogPanel(false);
    services_.text.Clear();
    services_.text.Present();
}

void EndingState::UpdateSmoke()
{
    SubScreenService &sub = services_.subScreen;
    for (int c = 0; c < chimneyCount_; c++)
    {
        for (int p = 0; p < kPuffsPerChimney; p++)
        {
            u32 sprite = puffSprites_[c * kPuffsPerChimney + p];
            int phase = (frame_ + c * 37 + p * (kPuffCycle / kPuffsPerChimney)) % kPuffCycle;
            int x = chimneys_[c].x + phase * kPuffDrift / kPuffCycle;
            int y = chimneys_[c].y - phase * kPuffRise / kPuffCycle;
            u32 size = phase < kPuffCycle / 3 ? ui::kIconSmokeSmall
                       : phase < 2 * kPuffCycle / 3 ? ui::kIconSmokeMedium
                                                    : ui::kIconSmokeLarge;
            sub.SetSpriteFrame(sprite, size);
            sub.MoveSprite(sprite, x - 8, y - 8);
            sub.ShowSprite(sprite, phase < kPuffCycle - 10);
        }
    }
}

void EndingState::ResetSkyLeaf(SkyLeaf &leaf, bool anywhere)
{
    // Enter from the top or the left edge and drift down to the right.
    if (anywhere)
    {
        leaf.x = random_.Range(0, 255) << 8;
        leaf.y = random_.Range(0, 191) << 8;
    }
    else if (random_.Chance(50))
    {
        leaf.x = random_.Range(-8, 200) * 256;
        leaf.y = -12 * 256;
    }
    else
    {
        leaf.x = -12 * 256;
        leaf.y = random_.Range(0, 150) << 8;
    }
    leaf.vx = random_.Range(80, 220);
    leaf.vy = random_.Range(60, 160);
    leaf.color = static_cast<u32>(random_.Range(0, 2));
    leaf.phase = random_.Range(0, 30);
}

void EndingState::UpdateSkyLeaves()
{
    SubScreenService &sub = services_.subScreen;
    for (int i = 0; i < kSkyLeaves; i++)
    {
        SkyLeaf &leaf = skyLeaves_[i];
        leaf.phase++;
        // A little sideways sway while falling.
        s32 sway = ((leaf.phase / 20) % 2 == 0) ? 40 : -40;
        leaf.x += leaf.vx + sway;
        leaf.y += leaf.vy;
        if ((leaf.x >> 8) > 264 || (leaf.y >> 8) > 200)
            ResetSkyLeaf(leaf, false);

        u32 flutter = ((leaf.phase / 12) % 2 == 0) ? 0 : 1;
        sub.SetSpriteFrame(skyLeafSprites_[i], ui::kIconSmallLeaf + leaf.color * 2 + flutter);
        sub.MoveSprite(skyLeafSprites_[i], (leaf.x >> 8) - 8, (leaf.y >> 8) - 8);
        sub.ShowSprite(skyLeafSprites_[i], true);
    }
}

void EndingState::Update()
{
    frame_++;
    fader_.Update();
    UpdateSmoke();
    UpdateSkyLeaves();
    LeafParticles::Area area = { { 0.5_fx, kSeatZ }, 3_fx, -3_fx, 1_fx, 2.4_fx };
    leaves_.Update(area, 60);

    nina_.Idle();
    mats_.Idle();
    cow_.Stand();

    int stepFrame = kFirstLineFrame + nextStep_ * kLineFrames;
    if (nextStep_ <= ending::kDialogLines && frame_ == stepFrame)
    {
        if (nextStep_ < ending::kDialogLines)
            ShowLine(nextStep_);
        else
            HideDialog();
        nextStep_++;
    }

    // Once Nina has spoken, any button leaves the picture for a new game.
    bool ninaHasSpoken = nextStep_ >= ending::kDialogLines;
    if (ninaHasSpoken && !leaving_ && services_.input.IsAnyButtonPressed())
    {
        leaving_ = true;
        fader_.FadeOut(kLeaveFadeFrames);
    }
    if (leaving_ && fader_.IsBlack())
    {
        leaving_ = false;
        machine_.StartNewGame();
    }
}

void EndingState::PlantForest()
{
    constexpr Fixed kCameraZ = 6.2_fx;
    // The slope must already be low enough that tree tops stay below the heads.
    constexpr Fixed kFirstRowZ = -4.5_fx;
    Random random(0x7EE5);
    cardCount_ = 0;

    auto plant = [&](Fixed x, Fixed z, Fixed distance) {
        if (cardCount_ >= kMaxTreeCards)
            return;
        TreeCard &card = cards_[cardCount_++];
        card.x = x;
        card.z = z;
        card.y = HillHeight(x, z);
        card.height = random.Range(1.5_fx, 2.2_fx) + distance * 0.035_fx;
        u32 roll = random.Next() % 100;
        card.kind = roll < 35 ? 0 : roll < 55 ? 1 : roll < 80 ? 2 : 3;
    };

    // Rows down the slope, across the valley and up the opposite slope. Further
    // away the rows get wider (the view widens), sparser and the trees bigger.
    for (Fixed z = kFirstRowZ; z > -26_fx && cardCount_ < kMaxTreeCards;)
    {
        Fixed distance = kCameraZ - z;
        Fixed halfWidth = distance * 0.62_fx + 1.5_fx;
        Fixed stepX = 0.7_fx + distance * 0.04_fx;
        for (Fixed x = -halfWidth; x <= halfWidth; x += stepX)
            plant(x + random.Range(-stepX * 0.4_fx, stepX * 0.4_fx), z + random.Range(-0.4_fx, 0.4_fx), distance);
        z -= 0.55_fx + distance * 0.03_fx;
    }
}

void EndingState::DrawTreeCards() const
{
    NE_PolyFormat(31, kCardPolygonId, static_cast<NE_LightEnum>(0), NE_CULL_NONE,
                  static_cast<NE_OtherFormatEnum>(NE_FOG_ENABLE));
    NE_MaterialUse(treeCards_);
    GFX_COLOR = kCardTint;

    for (int i = 0; i < cardCount_; i++)
    {
        const TreeCard &card = cards_[i];
        s32 halfWidth = (card.height * 0.45_fx).Raw();
        s32 height = card.height.Raw();
        int u = (card.kind % 2) * 32;
        int v = (card.kind / 2) * 32;

        NE_ViewPush();
        NE_ViewMoveI(card.x.Raw(), card.y.Raw(), card.z.Raw());

        GFX_BEGIN = GL_QUADS;
        GFX_TEX_COORD = TEXTURE_PACK(inttot16(u), inttot16(v));
        GFX_VERTEX16 = (static_cast<u32>(height & 0xFFFF) << 16) | static_cast<u32>(-halfWidth & 0xFFFF);
        GFX_VERTEX16 = 0;
        GFX_TEX_COORD = TEXTURE_PACK(inttot16(u), inttot16(v + 32));
        GFX_VERTEX_XY = static_cast<u32>(-halfWidth & 0xFFFF);
        GFX_TEX_COORD = TEXTURE_PACK(inttot16(u + 32), inttot16(v + 32));
        GFX_VERTEX_XY = static_cast<u32>(halfWidth & 0xFFFF);
        GFX_TEX_COORD = TEXTURE_PACK(inttot16(u + 32), inttot16(v));
        GFX_VERTEX_XY = (static_cast<u32>(height & 0xFFFF) << 16) | static_cast<u32>(halfWidth & 0xFFFF);

        NE_ViewPop();
    }
}

void EndingState::Draw3D()
{
    const RenderService &render = services_.render;
    NE_CameraUse(camera_);
    render.ClearObjectLight();

    NE_Model *hill = services_.assets.Model(ModelId::EndHill);
    NE_ModelSetCoordI(hill, 0, 0, 0);
    NE_ModelScaleI(hill, kHillScale.Raw(), kHillScale.Raw(), kHillScale.Raw());
    render.BeginPolygons(PolyGroup::Ground, 0, Lighting::Glow);
    NE_ModelDraw(hill);
    DrawTreeCards();
    leaves_.Draw(render);

    cow_.Draw(render);
    mats_.Draw(render);
    nina_.Draw(render);
}
