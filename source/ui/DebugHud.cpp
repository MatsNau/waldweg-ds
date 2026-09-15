#include "ui/DebugHud.h"

#include <stdio.h>

#include "entities/Mats.h"
#include "entities/Nina.h"
#include "render/RenderService.h"
#include "ui/TextService.h"
#include "ui/UiLayout.h"
#include "world/Forest.h"
#include "world/MushroomField.h"
#include "world/TimeOfDayService.h"

namespace {

// Fixed point value as text with one decimal, e.g. "-3.2".
void FormatFixed(char *out, size_t size, Fixed value)
{
    s32 raw = value.Raw();
    const char *sign = raw < 0 ? "-" : "";
    if (raw < 0)
        raw = -raw;
    s32 tenths = ((raw & (Fixed::kOne - 1)) * 10) >> Fixed::kShift;
    snprintf(out, size, "%s%ld.%ld", sign, static_cast<long>(raw >> Fixed::kShift),
             static_cast<long>(tenths));
}

} // namespace

bool DebugHud::Draw(const Nina &nina, const Mats &mats, const Forest &forest,
                    const MushroomField &mushrooms)
{
    if (refreshCountdown_-- > 0)
        return false;
    refreshCountdown_ = kRefreshFrames;

    TextService &text = services_.text;
    const RenderService &render = services_.render;
    char x[16];
    char z[16];
    char distance[16];
    int column = ui::kPanelColumn;
    int row = ui::kPanelRow;

    text.Clear();
    text.SetColor(TextColor::Speaker);
    text.Write(column, row, "Debug (START: aus)");
    text.SetColor(TextColor::Ink);

    text.Format(column, row + 1, "Poly %d/2048  Vtx %d", render.PolygonCount(), render.VertexCount());
    text.Format(column, row + 2, "Objekte %d/%d  Pilze %d", forest.LastDrawnProps(), forest.PropCount(),
                mushrooms.RemainingCount());

    FormatFixed(x, sizeof(x), nina.Position().x);
    FormatFixed(z, sizeof(z), nina.Position().z);
    FormatFixed(distance, sizeof(distance), mats.DistanceToNina());
    text.Format(column, row + 3, "Nina %s|%s Mats %s", x, z, distance);

    text.Format(column, row + 4, "%s  Nebel %04X", services_.timeOfDay.PhaseName(), render.FogDepth());
    text.Write(column, row + 5, "SEL Zeit R+SEL Nacht L+SEL Ende");
    return true;
}
