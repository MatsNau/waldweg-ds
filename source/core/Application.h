#pragma once

#include "audio/AudioService.h"
#include "core/InputService.h"
#include "core/Services.h"
#include "game/Game.h"
#include "render/AssetService.h"
#include "render/RenderService.h"
#include "ui/SubScreenService.h"
#include "ui/TextService.h"
#include "ui/TopTextService.h"
#include "world/TimeOfDayService.h"

// Boots the hardware and libraries, owns all services and runs the main loop.
class Application
{
public:
    [[noreturn]] void Run();

private:
    void Init();

    InputService input_;
    AssetService assets_;
    RenderService render_;
    SubScreenService subScreen_;
    TextService text_;
    TopTextService topText_;
    TimeOfDayService timeOfDay_{ render_ };
    AudioService audio_{ timeOfDay_ };
    Services services_{ input_, assets_, render_, text_, timeOfDay_, subScreen_, topText_, audio_ };
    Game game_{ services_ };
};
