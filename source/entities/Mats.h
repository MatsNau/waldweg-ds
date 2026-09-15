#pragma once

#include <array>

#include "content/Items.h"
#include "entities/Character.h"

class Nina;

// Follows Nina along her own path (breadcrumbs), so he walks around trees
// the same way she did, and stops at a comfortable distance.
class Mats : public Character
{
public:
    explicit Mats(const AssetService &assets);

    void Place(Vec2 position, Angle facing);
    void Update(const Nina &nina, const Forest &forest);

    // Shows an item Nina gave him (basket and bell in the right hand,
    // lantern in the left, scarf around the neck).
    void ShowItem(ItemId item);
    void ClearItems();

    Fixed DistanceToNina() const { return distanceToNina_; }

private:
    static constexpr int kTrailSize = 32;

    void RecordTrail(Vec2 ninaPosition);
    void ClearTrail() { trailCount_ = 0; }
    Vec2 NextTarget(Vec2 ninaPosition);

    std::array<Vec2, kTrailSize> trail_ = {};
    int trailHead_ = 0; // index of the oldest crumb
    int trailCount_ = 0;

    Fixed speed_;
    Fixed distanceToNina_;
};
