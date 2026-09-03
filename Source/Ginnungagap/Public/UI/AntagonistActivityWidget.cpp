#include "UI/AntagonistActivityWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/ProgressBar.h"
#include "Components/TextBlock.h"
#include "Versus/AntagonistActivityComponent.h"

namespace
{
UCanvasPanelSlot* PlaceAntagonistWidget(UCanvasPanel* Root, UWidget* Child,
	float X, float Y, float Width, float Height)
{
	UCanvasPanelSlot* Slot = Cast<UCanvasPanelSlot>(Root->AddChild(Child));
	if (Slot)
	{
		Slot->SetPosition(FVector2D(X, Y));
		Slot->SetSize(FVector2D(Width, Height));
	}
	return Slot;
}

void StyleAntagonistText(UTextBlock* Text, int32 Size, const FLinearColor& Color)
{
	FSlateFontInfo Font = Text->GetFont();
	Font.Size = Size;
	Text->SetFont(Font);
	Text->SetColorAndOpacity(FSlateColor(Color));
}
}

void UAntagonistActivityWidget::NativeConstruct()
{
	Super::NativeConstruct();
	BuildWidgetTree();
	SetVisibility(ESlateVisibility::Collapsed);
}

void UAntagonistActivityWidget::BuildWidgetTree()
{
	if (!WidgetTree || RootCanvas) return;
	RootCanvas = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass(), TEXT("AntagonistActivityRoot"));
	WidgetTree->RootWidget = RootCanvas;

	UBorder* Background = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("AntagonistActivityBackground"));
	Background->SetBrushColor(FLinearColor(0.005f, 0.01f, 0.012f, 0.94f));
	Background->SetPadding(FMargin(18));
	PlaceAntagonistWidget(RootCanvas, Background, 0, 0, 920, 560);

	TitleText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("AntagonistActivityTitle"));
	StyleAntagonistText(TitleText, 30, FLinearColor::White);
	PlaceAntagonistWidget(RootCanvas, TitleText, 28, 22, 860, 42);
	MotivationText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("AntagonistMotivation"));
	StyleAntagonistText(MotivationText, 15, FLinearColor(0.65f, 0.72f, 0.72f));
	MotivationText->SetAutoWrapText(true);
	PlaceAntagonistWidget(RootCanvas, MotivationText, 28, 70, 860, 52);

	ProgressBar = WidgetTree->ConstructWidget<UProgressBar>(UProgressBar::StaticClass(), TEXT("AntagonistActivityProgress"));
	PlaceAntagonistWidget(RootCanvas, ProgressBar, 28, 128, 860, 12);
	MechanicText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("AntagonistMechanicReadout"));
	StyleAntagonistText(MechanicText, 18, FLinearColor(0.84f, 0.9f, 0.88f));
	PlaceAntagonistWidget(RootCanvas, MechanicText, 28, 162, 860, 190);

	ResourceBarA = WidgetTree->ConstructWidget<UProgressBar>(UProgressBar::StaticClass(), TEXT("AntagonistResourceA"));
	ResourceBarB = WidgetTree->ConstructWidget<UProgressBar>(UProgressBar::StaticClass(), TEXT("AntagonistResourceB"));
	ResourceBarC = WidgetTree->ConstructWidget<UProgressBar>(UProgressBar::StaticClass(), TEXT("AntagonistResourceC"));
	PlaceAntagonistWidget(RootCanvas, ResourceBarA, 90, 372, 740, 14);
	PlaceAntagonistWidget(RootCanvas, ResourceBarB, 90, 404, 740, 14);
	PlaceAntagonistWidget(RootCanvas, ResourceBarC, 90, 436, 740, 14);

	InputText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("AntagonistInputPrompt"));
	StyleAntagonistText(InputText, 18, FLinearColor::White);
	InputText->SetJustification(ETextJustify::Center);
	PlaceAntagonistWidget(RootCanvas, InputText, 40, 478, 840, 52);
}

void UAntagonistActivityWidget::SetActivityComponent(UAntagonistActivityComponent* NewComponent)
{
	if (ActivityComponent)
	{
		ActivityComponent->OnActivityChanged.RemoveDynamic(this, &UAntagonistActivityWidget::HandleActivityChanged);
	}
	ActivityComponent = NewComponent;
	if (ActivityComponent)
	{
		ActivityComponent->OnActivityChanged.AddDynamic(this, &UAntagonistActivityWidget::HandleActivityChanged);
		UpdateFromSnapshot(ActivityComponent->GetSnapshot());
	}
}

void UAntagonistActivityWidget::HandleActivityChanged(const FAntagonistActivitySnapshot& Snapshot)
{
	UpdateFromSnapshot(Snapshot);
}

void UAntagonistActivityWidget::UpdateFromSnapshot(const FAntagonistActivitySnapshot& Snapshot)
{
	const bool bActive = Snapshot.State == EPlayerActivityState::Active;
	SetVisibility(bActive ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
	if (!bActive || !RootCanvas) return;

	const FLinearColor FactionColor = GetFactionColor(Snapshot.Faction);
	TitleText->SetText(Snapshot.DisplayName.ToUpper());
	TitleText->SetColorAndOpacity(FSlateColor(FactionColor));
	MotivationText->SetText(Snapshot.Motivation);
	ProgressBar->SetPercent(Snapshot.Progress);
	ProgressBar->SetFillColorAndOpacity(FactionColor);
	MechanicText->SetText(FText::FromString(BuildMechanicReadout(Snapshot)));
	ResourceBarA->SetPercent(Snapshot.ResourceBalance.X);
	ResourceBarB->SetPercent(Snapshot.ResourceBalance.Y);
	ResourceBarC->SetPercent(Snapshot.ResourceBalance.Z);
	ResourceBarA->SetFillColorAndOpacity(FactionColor);
	ResourceBarB->SetFillColorAndOpacity(FactionColor * 0.8f);
	ResourceBarC->SetFillColorAndOpacity(FactionColor * 0.6f);

	const bool bBalance = Snapshot.Mechanic == EAntagonistActivityMechanic::MetabolicBalance;
	const bool bTiming = Snapshot.Mechanic == EAntagonistActivityMechanic::AmbushTiming;
	ResourceBarA->SetVisibility(bBalance ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
	ResourceBarB->SetVisibility(bBalance ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
	ResourceBarC->SetVisibility(bBalance ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
	InputText->SetText(FText::FromString(bBalance
		? TEXT("[ E / F / 3 ] REGULATE   //   [ 4 ] COMMIT CYCLE   //   [ X ] ABORT")
		: bTiming
			? TEXT("[ E ] STRIKE INSIDE THE VIBRATION WINDOW   //   [ X ] ABORT")
			: TEXT("[ E / F / 3 / 4 ] RESOLVE PATTERN   //   [ X ] ABORT")));
}

FLinearColor UAntagonistActivityWidget::GetFactionColor(EAntagonistFaction Faction) const
{
	switch (Faction)
	{
	case EAntagonistFaction::Bloom: return FLinearColor(0.72f, 0.22f, 0.95f);
	case EAntagonistFaction::Pirates: return FLinearColor(1.0f, 0.58f, 0.08f);
	case EAntagonistFaction::Rebels: return FLinearColor(0.18f, 0.86f, 0.94f);
	case EAntagonistFaction::Alien: return FLinearColor(0.42f, 0.95f, 0.76f);
	default: return FLinearColor::White;
	}
}

FString UAntagonistActivityWidget::BuildMechanicReadout(const FAntagonistActivitySnapshot& Snapshot) const
{
	switch (Snapshot.Mechanic)
	{
	case EAntagonistActivityMechanic::MetabolicBalance:
		return FString::Printf(TEXT("METABOLIC EQUILIBRIUM\nNUTRIENT     %3.0f%%\nEXPOSURE     %3.0f%%\nCOHESION     %3.0f%%\n\nStabilize all three bands, then commit the feeding cycle.\nCYCLES %d / %d   //   ERRORS %d"),
			Snapshot.ResourceBalance.X * 100, Snapshot.ResourceBalance.Y * 100,
			Snapshot.ResourceBalance.Z * 100, Snapshot.CurrentStep, Snapshot.TotalSteps, Snapshot.Mistakes);
	case EAntagonistActivityMechanic::TerritoryWeave:
		return FString::Printf(TEXT("MYCELIAL GROWTH FRONT\nChoose the next viable seam without crossing a sterilized boundary.\nNODES JOINED %d / %d   //   SEVERED %d"),
			Snapshot.CurrentStep, Snapshot.TotalSteps, Snapshot.Mistakes);
	case EAntagonistActivityMechanic::NeuralMimicry:
		return FString::Printf(TEXT("HOST CADENCE RECONSTRUCTION\nRepeat pulse, breath, and speech timing. An incorrect cadence erases the last stable pattern.\nPATTERNS %d / %d   //   BREAKS %d"),
			Snapshot.CurrentStep, Snapshot.TotalSteps, Snapshot.Mistakes);
	case EAntagonistActivityMechanic::ScentTriangulation:
		return FString::Printf(TEXT("SCENT / HEAT / VIBRATION\nSeparate the newest trail from machinery echoes and pack residue.\nBEARINGS %d / %d   //   FALSE TRAILS %d"),
			Snapshot.CurrentStep, Snapshot.TotalSteps, Snapshot.Mistakes);
	case EAntagonistActivityMechanic::AmbushTiming:
		return FString::Printf(TEXT("VIBRATION WINDOW\nCURSOR %3.0f%%   //   STRIKE CENTER %3.0f%%   //   TOLERANCE %3.0f%%\nRemain still. Commit only when prey enters the kill lane.\nREADS %d / %d"),
			Snapshot.TimingCursor * 100, Snapshot.TimingWindowCenter * 100,
			Snapshot.TimingWindowWidth * 100, Snapshot.CurrentStep, Snapshot.TotalSteps);
	case EAntagonistActivityMechanic::TimedExtraction:
		return FString::Printf(TEXT("EXTRACTION IN PROGRESS\nHold the site while cargo is cut free.\nTRANSFER %3.0f%%"), Snapshot.Progress * 100);
	default:
		return FString::Printf(TEXT("SYSTEM INTRUSION\nResolve the hostile channel pattern before lockout.\nSTEPS %d / %d   //   ERRORS %d"),
			Snapshot.CurrentStep, Snapshot.TotalSteps, Snapshot.Mistakes);
	}
}

