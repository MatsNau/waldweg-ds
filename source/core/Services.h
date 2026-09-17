#pragma once

class InputService;
class AssetService;
class AudioService;
class RenderService;
class TextService;
class TimeOfDayService;
class SubScreenService;
class TopTextService;

// Shared engine services, owned by Application and handed to the game by reference.
struct Services
{
    InputService &input;
    AssetService &assets;
    RenderService &render;
    TextService &text;
    TimeOfDayService &timeOfDay;
    SubScreenService &subScreen;
    TopTextService &topText;
    AudioService &audio;
};
