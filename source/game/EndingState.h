#pragma once

#include <array>

#include <NEMain.h>

#include "core/Services.h"
#include "entities/Mats.h"
#include "entities/Nina.h"
#include "entities/Shroomchen.h"
#include "game/GameState.h"
#include "core/Random.h"
#include "ui/ScreenFader.h"
#include "world/LeafParticles.h"

// The final picture, spread over both screens: the sunrise sky with the
// village and its smoking chimneys on the upper screen (drawn), the hill with
// Nina, Mats and Shroomchen seen from behind on the lower screen (3D).
// Mats and Nina talk a little, then "Ende".
class EndingState : public GameState
{
public:
    EndingState(Services &services, StateMachine &machine);

    void Init();

    void Enter() override;
    void Exit() override;
    void Update() override;
    void Draw3D() override;

private:
    static constexpr int kMaxChimneys = 8;
    static constexpr int kPuffsPerChimney = 2;
    static constexpr int kSkyLeaves = 7;
    // Budget: characters + Shroomchen + hill ~1400 polygons / ~4200 vertices, so
    // ~380 cards keep the picture under 2048 polygons / 6144 vertices.
    static constexpr int kMaxTreeCards = 380;

    // A drawn tree standing on the slope (one textured quad).
    struct TreeCard
    {
        Fixed x, y, z;
        Fixed height;
        u8 kind; // 0 orange, 1 red, 2 yellow, 3 fir
    };

    struct SkyLeaf
    {
        s32 x, y;   // 24.8 fixed point pixels
        s32 vx, vy;
        u32 color;  // 0-2
        int phase;
    };

    struct Chimney
    {
        int x;
        int y;
    };

    void LoadChimneys();
    void ShowLine(int index);
    void HideDialog();
    void UpdateSmoke();
    void UpdateSkyLeaves();
    void ResetSkyLeaf(SkyLeaf &leaf, bool anywhere);
    void PlantForest();
    void DrawTreeCards() const;

    Services &services_;
    StateMachine &machine_;
    Shroomchen cow_;
    Nina nina_;
    Mats mats_;
    ScreenFader fader_;
    NE_Camera *camera_ = nullptr;
    NE_Material *treeCards_ = nullptr;
    NE_Material *hillMaterial_ = nullptr;
    std::array<TreeCard, kMaxTreeCards> cards_ = {};
    int cardCount_ = 0;

    std::array<Chimney, kMaxChimneys> chimneys_ = {};
    int chimneyCount_ = 0;
    std::array<u32, kMaxChimneys * kPuffsPerChimney> puffSprites_ = {};
    std::array<SkyLeaf, kSkyLeaves> skyLeaves_ = {};
    std::array<u32, kSkyLeaves> skyLeafSprites_ = {};
    bool spritesCreated_ = false;
    Random random_{ 0xFA11 };
    LeafParticles leaves_;

    int frame_ = 0;
    int nextStep_ = 0;
    bool leaving_ = false;
};
