#include "entities/Character.h"

#include "render/RenderService.h"
#include "world/Forest.h"

void Character::Draw(const RenderService &render) const
{
    render.LightObject(position_);
    rig_.Draw(render, position_, facing_, elevation_);
}

void Character::Place(Vec2 position, Angle facing)
{
    position_ = position;
    facing_ = facing;
}

void Character::Walk(Vec2 delta, const Forest &forest)
{
    if (delta.IsZero())
    {
        Stand();
        return;
    }

    Vec2 resolved = forest.ResolveCollision(position_ + delta, kRadius);
    Fixed moved = (resolved - position_).Length();
    position_ = resolved;

    facing_ = facing_.TurnedTowards(Angle::FromDirection(delta), kTurnSpeed);
    rig_.Update(moved);
}

void Character::Stand()
{
    rig_.Update(0_fx);
}
