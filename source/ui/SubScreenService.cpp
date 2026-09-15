#include "ui/SubScreenService.h"

#include <stdio.h>

#include <nds.h>
#include <nf_lib.h>

#include "core/Fatal.h"

namespace {

using namespace ui;

struct SheetInfo
{
    const char *path;
    u32 frameSize;
};

// Same order as ui::Sheet. RAM slot, VRAM slot and palette all use the index.
constexpr SheetInfo kSheets[] = {
    { "ui/spr_icons", 16 },
    { "ui/spr_items", 32 },
};

constexpr u32 kMapTileCount = 36;

} // namespace

void SubScreenService::Init()
{
    NF_InitTiledBgBuffers();
    NF_InitTiledBgSys(kSubScreen);
    NF_InitSpriteBuffers();
    NF_InitSpriteSys(kSubScreen);
    NF_InitTextSys(kSubScreen);

    // The forest map: a blank 512x512 map filled by ForestMap from the tileset.
    NF_LoadTilesForBg("ui/map_tiles", "map", 512, 512, 0, kMapTileCount - 1);
    NF_LoadTiledBg("ui/bg_bar", "bar", 256, 256);
    NF_LoadTiledBg("ui/bg_dialog", "dialog", 256, 256);

    NF_CreateTiledBg(kSubScreen, kLayerMap, "map");
    NF_CreateTiledBg(kSubScreen, kLayerBar, "bar");
    NF_CreateTiledBg(kSubScreen, kLayerDialog, "dialog");
    ShowDialogPanel(false);

    for (u32 i = 0; i < static_cast<u32>(Sheet::Count); i++)
    {
        const SheetInfo &sheet = kSheets[i];
        NF_LoadSpriteGfx(sheet.path, i, sheet.frameSize, sheet.frameSize);
        NF_LoadSpritePal(sheet.path, i);
        // false = copy all frames to VRAM. With true only one frame is in VRAM
        // and every sprite using the sheet would show the same frame.
        NF_VramSpriteGfx(kSubScreen, i, i, false);
        NF_VramSpritePal(kSubScreen, i, i);
    }

    setBackdropColorSub(RGB15(24, 20, 14));
}

u32 SubScreenService::CreateSprite(Sheet sheet, u32 frame, int x, int y, u32 priority)
{
    if (nextSprite_ >= kMaxSprites)
        Fatal("Zu viele Sprites auf dem unteren Bildschirm.");

    u32 id = nextSprite_++;
    u32 slot = static_cast<u32>(sheet);
    NF_CreateSprite(kSubScreen, id, slot, slot, x, y);
    NF_SpriteFrame(kSubScreen, id, frame);
    NF_SpriteLayer(kSubScreen, id, priority);
    return id;
}

void SubScreenService::SetSpriteFrame(u32 id, u32 frame)
{
    NF_SpriteFrame(kSubScreen, id, frame);
}

void SubScreenService::MoveSprite(u32 id, int x, int y)
{
    NF_MoveSprite(kSubScreen, id, x, y);
}

void SubScreenService::ShowSprite(u32 id, bool show)
{
    NF_ShowSprite(kSubScreen, id, show);
}

void SubScreenService::SetSpritePriority(u32 id, u32 priority)
{
    NF_SpriteLayer(kSubScreen, id, priority);
}

void SubScreenService::ShowDialogPanel(bool show)
{
    if (show)
        NF_ShowBg(kSubScreen, kLayerDialog);
    else
        NF_HideBg(kSubScreen, kLayerDialog);
}

void SubScreenService::EnterBookMode()
{
    NF_HideBg(kSubScreen, kLayerMap);
    NF_HideBg(kSubScreen, kLayerBar);
    NF_DeleteTiledBg(kSubScreen, kLayerDialog); // frees VRAM for the page
    REG_DISPCNT_SUB &= ~DISPLAY_SPR_ACTIVE;
    pageLoaded_ = false;
}

void SubScreenService::ShowBookPage(int page)
{
    char name[16];
    snprintf(name, sizeof(name), "page%d", page);
    ShowBookImage(name);
}

void SubScreenService::ShowBookImage(const char *name)
{
    char path[32];
    snprintf(path, sizeof(path), "book/%s", name);

    if (pageLoaded_)
    {
        NF_DeleteTiledBg(kSubScreen, kLayerDialog);
        NF_UnloadTiledBg("page");
    }
    NF_LoadTiledBg(path, "page", 256, 256);
    NF_CreateTiledBg(kSubScreen, kLayerDialog, "page");
    pageLoaded_ = true;
}

void SubScreenService::ExitBookMode()
{
    if (pageLoaded_)
    {
        NF_DeleteTiledBg(kSubScreen, kLayerDialog);
        NF_UnloadTiledBg("page");
        pageLoaded_ = false;
    }
    NF_CreateTiledBg(kSubScreen, kLayerDialog, "dialog");
    ShowDialogPanel(false);
    NF_ShowBg(kSubScreen, kLayerMap);
    NF_ShowBg(kSubScreen, kLayerBar);
    REG_DISPCNT_SUB |= DISPLAY_SPR_ACTIVE;
}

void SubScreenService::EnterEndingMode()
{
    if (pageLoaded_)
    {
        NF_DeleteTiledBg(kSubScreen, kLayerDialog);
        NF_UnloadTiledBg("page");
        pageLoaded_ = false;
        NF_CreateTiledBg(kSubScreen, kLayerDialog, "dialog");
    }
    ShowDialogPanel(false);
    NF_HideBg(kSubScreen, kLayerBar);

    NF_DeleteTiledBg(kSubScreen, kLayerMap);
    NF_LoadTiledBg("book/ending_sky", "ending", 256, 256);
    NF_CreateTiledBg(kSubScreen, kLayerMap, "ending");
    NF_ScrollBg(kSubScreen, kLayerMap, 0, 0);

    for (u32 id = 0; id < nextSprite_; id++)
        NF_ShowSprite(kSubScreen, id, false);
    REG_DISPCNT_SUB |= DISPLAY_SPR_ACTIVE;
}

void SubScreenService::ExitEndingMode()
{
    for (u32 id = 0; id < nextSprite_; id++)
        NF_ShowSprite(kSubScreen, id, false);
    ShowDialogPanel(false);

    NF_DeleteTiledBg(kSubScreen, kLayerMap);
    NF_UnloadTiledBg("ending");
    NF_CreateTiledBg(kSubScreen, kLayerMap, "map");
    NF_ShowBg(kSubScreen, kLayerBar);
}

void SubScreenService::PrepareFrame()
{
    NF_SpriteOamSet(kSubScreen);
}

void SubScreenService::AfterVBlank()
{
    oamUpdate(&oamSub);
}
