#pragma once

#include "entities/Character.h"

class InputService;

// The player character.
class Nina : public Character
{
public:
    static constexpr Fixed kWalkSpeed = 0.055_fx; // units per frame

    explicit Nina(const AssetService &assets);

    void Update(const InputService &input, const Forest &forest);

    // The wool hat she puts on when it gets cold.
    void SetWearingHat(bool wearing);
};
