#include "game/IdentifyState.h"

#include <NEMain.h>

#include "core/InputService.h"
#include "render/RenderService.h"
#include "world/TimeOfDayService.h"

namespace {

// Warm, neutral light for looking at a mushroom up close, independent of the
// time of day in the forest.
const Atmosphere kInspectionAtmosphere = {
    RGB15(26, 22, 15), RGB15(31, 30, 27), RGB15(13, 12, 11), RGB15(6, 4, 3),
    floattov10(-0.45), floattov10(-0.55), floattov10(-0.7), 0x7FFF, 0, 0,
};

} // namespace

IdentifyState::IdentifyState(Services &services, StateMachine &machine, IdentifySession &session)
    : services_(services),
      machine_(machine),
      session_(session),
      book_(services.subScreen, services.text),
      view_(services.assets)
{
}

void IdentifyState::Init()
{
    view_.Init();
}

void IdentifyState::Enter()
{
    finished_ = false;
    session_.outcome = IdentifySession::Outcome::None;

    NE_MainScreenSetOnBottom();
    services_.render.SetFogEnabled(false);
    services_.render.SetPointLight(nullptr);
    services_.render.ApplyAtmosphere(kInspectionAtmosphere);

    view_.Show(Species(session_.actual).detailModel);
    book_.Open(lastPage_);
}

void IdentifyState::Exit()
{
    lastPage_ = book_.Page();
    book_.Close();

    NE_MainScreenSetOnTop();
    services_.render.SetFogEnabled(true);
    services_.timeOfDay.Reapply();
}

void IdentifyState::Update()
{
    if (finished_)
        return;

    const InputService &input = services_.input;

    // Turn pages with L/R, the D-pad or the mirrored face buttons.
    if (input.IsPressed(Button::L) || input.IsPressed(Button::Left) || input.IsPressed(Button::Y))
        book_.Turn(-1);
    if (input.IsPressed(Button::R) || input.IsPressed(Button::Right) || input.IsPressed(Button::A))
        book_.Turn(+1);

    switch (view_.Update(input))
    {
        case InspectionView::Action::Back:
            Finish(IdentifySession::Outcome::Cancelled);
            break;
        case InspectionView::Action::Choose:
            session_.chosen = book_.PageSpecies();
            Finish(IdentifySession::Outcome::Chosen);
            break;
        case InspectionView::Action::None:
            if (input.IsPressed(Button::B))
                Finish(IdentifySession::Outcome::Cancelled);
            break;
    }
}

void IdentifyState::Finish(IdentifySession::Outcome outcome)
{
    finished_ = true;
    session_.outcome = outcome;
    machine_.ChangeState(StateId::Explore);
}

void IdentifyState::Draw3D()
{
    view_.Draw(services_.render);
}
