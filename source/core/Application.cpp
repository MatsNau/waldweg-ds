#include "core/Application.h"

#include <filesystem.h>
#include <nds.h>
#include <nf_lib.h>

#include "core/Fatal.h"

namespace {

constexpr int kMainScreen = 0;
constexpr int kSubScreen = 1;

} // namespace

void Application::Init()
{
    // Same order as the Nitro Engine "using_nflib" template.
    NF_Set2D(kMainScreen, 0);
    NF_Set2D(kSubScreen, 0);

    if (!nitroFSInit(nullptr))
        Fatal("NitroFS konnte nicht gestartet werden.");
    NF_SetRootFolder("NITROFS");

    irqEnable(IRQ_HBLANK);
    irqSet(IRQ_VBLANK, NE_VBLFunc);
    irqSet(IRQ_HBLANK, NE_HBLFunc);

    render_.Init();
    assets_.LoadAll();
    render_.AddLitMaterial(assets_.PaletteMaterial());
    topText_.Init();
    subScreen_.Init();
    text_.Init();

    game_.Init();
}

void Application::Run()
{
    Init();

    while (true)
    {
        NE_WaitForVBL(static_cast<NE_UpdateFlags>(0));
        subScreen_.AfterVBlank();

        input_.Update();
        game_.Update();
        timeOfDay_.Update();

        subScreen_.PrepareFrame();
        render_.Render(game_);
    }
}
