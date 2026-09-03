#include "UI/FirstLaunchCharacterCreationWidget.h"
#include "Components/EditableTextBox.h"
#include "Components/Button.h"
#include "Components/TextBlock.h"
#include "Meta/CharacterProfileSubsystem.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetRenderingLibrary.h"
#include "Components/Image.h"
#include "Engine/SceneCapture2D.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Components/ChildActorComponent.h"
#include "Engine/TextureRenderTarget2D.h"
#include "CoopSurvivalCharacter.h"
#include "Blueprint/WidgetTree.h"
#include "Components/VerticalBox.h"
#include "Components/HorizontalBox.h"
#include "Components/SizeBox.h"
#include "Components/Border.h"
#include "Components/VerticalBoxSlot.h"
#include "Components/SafeZone.h"
#include "UI/MenuVisualStyle.h"
#include "Input/Reply.h"

void UFirstLaunchCharacterCreationWidget::NativeConstruct()
{
	Super::NativeConstruct();
	BuildFallbackLayout();

	if (ConfirmButton)
	{
		ConfirmButton->OnClicked.AddDynamic(this, &UFirstLaunchCharacterCreationWidget::OnConfirmClicked);
	}
	if (ScienceRoleButton) ScienceRoleButton->OnClicked.AddDynamic(this, &UFirstLaunchCharacterCreationWidget::OnScienceRoleClicked);
	if (EngineeringRoleButton) EngineeringRoleButton->OnClicked.AddDynamic(this, &UFirstLaunchCharacterCreationWidget::OnEngineeringRoleClicked);
	if (MedicalRoleButton) MedicalRoleButton->OnClicked.AddDynamic(this, &UFirstLaunchCharacterCreationWidget::OnMedicalRoleClicked);
	if (SecurityRoleButton) SecurityRoleButton->OnClicked.AddDynamic(this, &UFirstLaunchCharacterCreationWidget::OnSecurityRoleClicked);
	if (RotatePreviewLeftButton) RotatePreviewLeftButton->OnClicked.AddDynamic(this, &UFirstLaunchCharacterCreationWidget::OnRotatePreviewLeft);
	if (RotatePreviewRightButton) RotatePreviewRightButton->OnClicked.AddDynamic(this, &UFirstLaunchCharacterCreationWidget::OnRotatePreviewRight);
	if (PreviousMetaHumanButton) PreviousMetaHumanButton->OnClicked.AddDynamic(this, &UFirstLaunchCharacterCreationWidget::OnPreviousMetaHumanClicked);
	if (NextMetaHumanButton) NextMetaHumanButton->OnClicked.AddDynamic(this, &UFirstLaunchCharacterCreationWidget::OnNextMetaHumanClicked);
	if (BackButton) BackButton->OnClicked.AddDynamic(this, &UFirstLaunchCharacterCreationWidget::OnBackClicked);
	if (CharacterNameInput) CharacterNameInput->OnTextChanged.AddDynamic(this, &UFirstLaunchCharacterCreationWidget::OnCharacterNameChanged);

	// Seed selections from CharacterDraft rather than hardcoded defaults: when this widget follows
	// UCharacterCreatorWidget in the identity-confirmation flow, MenuManagerSubsystem populates
	// CharacterDraft via SetCharacterDraft() before construction, and its selections (including the
	// FacePreset-derived MetaHumanPresetId) should carry forward instead of being discarded. When
	// reached directly, CharacterDraft's own field defaults match what was hardcoded here before.
	SelectedAppearance = CharacterDraft.AppearanceVariant;
	SelectedSuitRole = CharacterDraft.SuitRole;
	SelectedMetaHumanPresetId = CharacterDraft.MetaHumanPresetId;
	CreateSuitPreview();
	UpdateAppearanceUI();
	SetIsFocusable(true);
	if (CharacterNameInput) CharacterNameInput->SetKeyboardFocus();
}

void UFirstLaunchCharacterCreationWidget::NativeDestruct()
{
	if (ConfirmButton)
	{
		ConfirmButton->OnClicked.RemoveDynamic(this, &UFirstLaunchCharacterCreationWidget::OnConfirmClicked);
	}
	if (ScienceRoleButton) ScienceRoleButton->OnClicked.RemoveDynamic(this, &UFirstLaunchCharacterCreationWidget::OnScienceRoleClicked);
	if (EngineeringRoleButton) EngineeringRoleButton->OnClicked.RemoveDynamic(this, &UFirstLaunchCharacterCreationWidget::OnEngineeringRoleClicked);
	if (MedicalRoleButton) MedicalRoleButton->OnClicked.RemoveDynamic(this, &UFirstLaunchCharacterCreationWidget::OnMedicalRoleClicked);
	if (SecurityRoleButton) SecurityRoleButton->OnClicked.RemoveDynamic(this, &UFirstLaunchCharacterCreationWidget::OnSecurityRoleClicked);
	if (RotatePreviewLeftButton) RotatePreviewLeftButton->OnClicked.RemoveDynamic(this, &UFirstLaunchCharacterCreationWidget::OnRotatePreviewLeft);
	if (RotatePreviewRightButton) RotatePreviewRightButton->OnClicked.RemoveDynamic(this, &UFirstLaunchCharacterCreationWidget::OnRotatePreviewRight);
	if (PreviousMetaHumanButton) PreviousMetaHumanButton->OnClicked.RemoveDynamic(this, &UFirstLaunchCharacterCreationWidget::OnPreviousMetaHumanClicked);
	if (NextMetaHumanButton) NextMetaHumanButton->OnClicked.RemoveDynamic(this, &UFirstLaunchCharacterCreationWidget::OnNextMetaHumanClicked);
	if (BackButton) BackButton->OnClicked.RemoveDynamic(this, &UFirstLaunchCharacterCreationWidget::OnBackClicked);
	if (CharacterNameInput) CharacterNameInput->OnTextChanged.RemoveDynamic(this, &UFirstLaunchCharacterCreationWidget::OnCharacterNameChanged);
	DestroySuitPreview();

	Super::NativeDestruct();
}

void UFirstLaunchCharacterCreationWidget::OnConfirmClicked()
{
	ValidateAndCreateCharacter();
}

void UFirstLaunchCharacterCreationWidget::OnAppearanceSelected(ECharacterAppearance Appearance)
{
	SelectedAppearance = Appearance;
	UpdateAppearanceUI();
}

void UFirstLaunchCharacterCreationWidget::OnSuitRoleSelected(EPressureSuitRole SuitRole)
{
	SelectedSuitRole = SuitRole;
	UpdateAppearanceUI();
}

bool UFirstLaunchCharacterCreationWidget::OnMetaHumanPresetSelected(FName PresetId)
{
	if (!PreviewCharacter || !PreviewCharacter->SetMetaHumanPreset(PresetId))
	{
		return false;
	}
	SelectedMetaHumanPresetId = PresetId;
	// Keep CharacterDraft.FacePreset in step with the live selection so the preview stays
	// consistent regardless of which resolution path (preset ID vs. FacePreset enum) is active.
	CharacterDraft.FacePreset = FacePresetFromMetaHumanPresetId(PresetId);
	UpdateAppearanceUI();
	return true;
}

void UFirstLaunchCharacterCreationWidget::OnScienceRoleClicked() { OnSuitRoleSelected(EPressureSuitRole::Scientist); }
void UFirstLaunchCharacterCreationWidget::OnEngineeringRoleClicked() { OnSuitRoleSelected(EPressureSuitRole::Engineering); }
void UFirstLaunchCharacterCreationWidget::OnMedicalRoleClicked() { OnSuitRoleSelected(EPressureSuitRole::Medical); }
void UFirstLaunchCharacterCreationWidget::OnSecurityRoleClicked() { OnSuitRoleSelected(EPressureSuitRole::Security); }
void UFirstLaunchCharacterCreationWidget::OnRotatePreviewLeft()
{
	if (PreviewCharacter) PreviewCharacter->AddActorLocalRotation(FRotator(0, -20, 0));
	RefreshSuitPreview();
}

void UFirstLaunchCharacterCreationWidget::OnRotatePreviewRight()
{
	if (PreviewCharacter) PreviewCharacter->AddActorLocalRotation(FRotator(0, 20, 0));
	RefreshSuitPreview();
}

void UFirstLaunchCharacterCreationWidget::OnPreviousMetaHumanClicked() { SelectAdjacentMetaHuman(-1); }
void UFirstLaunchCharacterCreationWidget::OnNextMetaHumanClicked() { SelectAdjacentMetaHuman(1); }

void UFirstLaunchCharacterCreationWidget::SelectAdjacentMetaHuman(int32 Direction)
{
	const FString Current = SelectedMetaHumanPresetId.ToString();
	int32 CurrentIndex = FCString::Atoi(*Current.Right(2));
	CurrentIndex = FMath::Clamp(CurrentIndex, 1, 12);
	for (int32 Offset = 1; Offset <= 12; ++Offset)
	{
		const int32 CandidateIndex = ((CurrentIndex - 1 + Direction * Offset) % 12 + 12) % 12 + 1;
		const FName Candidate(*FString::Printf(TEXT("PlayerFace%02d"), CandidateIndex));
		if (OnMetaHumanPresetSelected(Candidate))
		{
			return;
		}
	}
}

void UFirstLaunchCharacterCreationWidget::UpdateAppearanceUI()
{
	if (SelectedSuitRoleText)
	{
		const UEnum* RoleEnum = StaticEnum<EPressureSuitRole>();
		SelectedSuitRoleText->SetText(RoleEnum ? RoleEnum->GetDisplayNameTextByValue(static_cast<int64>(SelectedSuitRole)) : FText::GetEmpty());
	}
	if (SelectedMetaHumanText)
	{
		SelectedMetaHumanText->SetText(FText::FromString(
			FString::Printf(TEXT("FACE PRESET  //  %s"), *SelectedMetaHumanPresetId.ToString())));
	}
	RefreshSuitPreview();
}

void UFirstLaunchCharacterCreationWidget::BuildFallbackLayout()
{
	if (!WidgetTree || WidgetTree->RootWidget) return;
	UBorder* Background = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("CharacterCreationBackground"));
	GinnungagapMenuStyle::ApplyTerminalPanel(Background);
	Background->SetPadding(FMargin(72.0f, 32.0f));
	USafeZone* Safe=WidgetTree->ConstructWidget<USafeZone>(USafeZone::StaticClass(),TEXT("SafeZone"));Safe->AddChild(Background);WidgetTree->RootWidget=Safe;
	UVerticalBox* Root = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("CharacterCreationRoot"));
	Background->SetContent(Root);
	auto AddText = [this](const TCHAR* Name, const TCHAR* Copy, int32 Size, const FLinearColor& Color)
	{
		UTextBlock* Text = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), Name);
		Text->SetText(FText::FromString(Copy));
		GinnungagapMenuStyle::ApplyTerminalText(Text,Size,Color,Size<=12);
		return Text;
	};
	Root->AddChildToVerticalBox(AddText(TEXT("StepText"), TEXT("CREW REGISTRY  //  DUTY ASSIGNMENT"), 12, GinnungagapMenuStyle::SafetyAmber));
	UTextBlock* Heading = AddText(TEXT("HeadingText"), TEXT("ASSIGN OPERATOR CLASS"), 34, GinnungagapMenuStyle::CryoWhite);
	if (UVerticalBoxSlot* HeadingSlot = Root->AddChildToVerticalBox(Heading)) HeadingSlot->SetPadding(FMargin(0, 10, 0, 24));

	SelectedSuitRoleText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("SelectedSuitRoleText"));
	GinnungagapMenuStyle::ApplyTerminalText(SelectedSuitRoleText,14,GinnungagapMenuStyle::SafetyAmber,true);
	Root->AddChildToVerticalBox(SelectedSuitRoleText);
	SelectedMetaHumanText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("SelectedMetaHumanText"));
	SelectedMetaHumanText->SetColorAndOpacity(FSlateColor(FLinearColor(0.70f, 0.78f, 0.82f)));
	Root->AddChildToVerticalBox(SelectedMetaHumanText);
	USizeBox* PreviewSize = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass(), TEXT("PreviewSize"));
	PreviewSize->SetWidthOverride(320.0f);
	PreviewSize->SetHeightOverride(280.0f);
	SuitPreviewImage = WidgetTree->ConstructWidget<UImage>(UImage::StaticClass(), TEXT("SuitPreviewImage"));
	PreviewSize->AddChild(SuitPreviewImage);
	Root->AddChildToVerticalBox(PreviewSize);

	UHorizontalBox* RoleRow = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("SuitRoleRow"));
	Root->AddChildToVerticalBox(RoleRow);
	auto AddButton = [this](UHorizontalBox* Row, const TCHAR* Name, const TCHAR* Label, UButton*& OutButton)
	{
		OutButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), Name);
		GinnungagapMenuStyle::ApplyButton(OutButton,FString(Name).Contains(TEXT("Confirm")));
		UTextBlock* Text = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
		Text->SetText(FText::FromString(Label));
		OutButton->AddChild(Text);
		Row->AddChildToHorizontalBox(OutButton);
	};
	AddButton(RoleRow, TEXT("ScienceRoleButton"), TEXT("Science"), ScienceRoleButton);
	AddButton(RoleRow, TEXT("EngineeringRoleButton"), TEXT("Engineering"), EngineeringRoleButton);
	AddButton(RoleRow, TEXT("MedicalRoleButton"), TEXT("Medical"), MedicalRoleButton);
	AddButton(RoleRow, TEXT("SecurityRoleButton"), TEXT("Security"), SecurityRoleButton);

	UHorizontalBox* FaceRow = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("MetaHumanPresetRow"));
	Root->AddChildToVerticalBox(FaceRow);
	AddButton(FaceRow, TEXT("PreviousMetaHumanButton"), TEXT("< Previous Face"), PreviousMetaHumanButton);
	AddButton(FaceRow, TEXT("NextMetaHumanButton"), TEXT("Next Face >"), NextMetaHumanButton);

	UHorizontalBox* RotateRow = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("PreviewRotateRow"));
	Root->AddChildToVerticalBox(RotateRow);
	AddButton(RotateRow, TEXT("RotatePreviewLeftButton"), TEXT("Rotate Left"), RotatePreviewLeftButton);
	AddButton(RotateRow, TEXT("RotatePreviewRightButton"), TEXT("Rotate Right"), RotatePreviewRightButton);

	CharacterNameInput = WidgetTree->ConstructWidget<UEditableTextBox>(UEditableTextBox::StaticClass(), TEXT("CharacterNameInput"));
	CharacterNameInput->SetText(FText::FromString(CharacterDraft.CharacterName));
	CharacterNameInput->SetIsReadOnly(true);
	Root->AddChildToVerticalBox(CharacterNameInput);
	CharacterCountText = AddText(TEXT("CharacterCountText"), TEXT("IDENTITY RECORD LOCKED // CLASS ASSIGNMENT ONLY"), 11, GinnungagapMenuStyle::MutedSteel);
	Root->AddChildToVerticalBox(CharacterCountText);
	ValidationText = AddText(TEXT("ValidationText"), TEXT(""), 12, GinnungagapMenuStyle::FaultRed);
	Root->AddChildToVerticalBox(ValidationText);
	UHorizontalBox* ConfirmRow = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("ConfirmRow"));
	Root->AddChildToVerticalBox(ConfirmRow);
	AddButton(ConfirmRow, TEXT("BackButton"), TEXT("<  RETURN TO IDENTITY"), BackButton);
	AddButton(ConfirmRow, TEXT("ConfirmButton"), TEXT("CONFIRM DUTY ASSIGNMENT  >"), ConfirmButton);
}

void UFirstLaunchCharacterCreationWidget::CreateSuitPreview()
{
	if (!SuitPreviewImage || !GetWorld()) return;
	PreviewRenderTarget = UKismetRenderingLibrary::CreateRenderTarget2D(
		this, 512, 512, ETextureRenderTargetFormat::RTF_RGBA8, FLinearColor(0.008f, 0.012f, 0.018f, 1.0f));
	if (!PreviewRenderTarget) return;
	SuitPreviewImage->SetBrushResourceObject(PreviewRenderTarget);

	const FVector PreviewOrigin(0, 0, -100000.0f);
	PreviewCharacter = GetWorld()->SpawnActor<ACoopSurvivalCharacter>(ACoopSurvivalCharacter::StaticClass(), PreviewOrigin, FRotator::ZeroRotator);
	PreviewCapture = GetWorld()->SpawnActor<ASceneCapture2D>(PreviewOrigin + FVector(360, 0, 75), FRotator(0, 180, 0));
	if (!PreviewCharacter || !PreviewCapture) return;
	PreviewCharacter->SetReplicates(false);
	PreviewCharacter->SetActorEnableCollision(false);
	PreviewCapture->GetCaptureComponent2D()->TextureTarget = PreviewRenderTarget;
	PreviewCapture->GetCaptureComponent2D()->CaptureSource = ESceneCaptureSource::SCS_FinalColorLDR;
	PreviewCapture->GetCaptureComponent2D()->FOVAngle = 38.0f;
	PreviewCapture->GetCaptureComponent2D()->bCaptureEveryFrame = false;
	PreviewCapture->GetCaptureComponent2D()->bCaptureOnMovement = false;
	PreviewCapture->GetCaptureComponent2D()->ShowOnlyActorComponents(PreviewCharacter);
}

void UFirstLaunchCharacterCreationWidget::RefreshSuitPreview()
{
	if (PreviewCharacter)
	{
		CharacterDraft.SuitRole = SelectedSuitRole;
		PreviewCharacter->ApplyCharacterIdentity(CharacterDraft);
		PreviewCharacter->SetPressureSuitRole(SelectedSuitRole);
		PreviewCharacter->SetMetaHumanPreset(SelectedMetaHumanPresetId);
	}
	if (PreviewCapture)
	{
		USceneCaptureComponent2D* Capture = PreviewCapture->GetCaptureComponent2D();
		Capture->ClearShowOnlyComponents();
		if (PreviewCharacter)
		{
			Capture->ShowOnlyActorComponents(PreviewCharacter);
			if (UChildActorComponent* ChildComponent = PreviewCharacter->FindComponentByClass<UChildActorComponent>())
			{
				if (AActor* MetaHumanActor = ChildComponent->GetChildActor())
				{
					Capture->ShowOnlyActorComponents(MetaHumanActor);
				}
			}
		}
		Capture->CaptureScene();
	}
}

void UFirstLaunchCharacterCreationWidget::DestroySuitPreview()
{
	if (PreviewCapture) PreviewCapture->Destroy();
	if (PreviewCharacter) PreviewCharacter->Destroy();
	PreviewCapture = nullptr;
	PreviewCharacter = nullptr;
	PreviewRenderTarget = nullptr;
}

void UFirstLaunchCharacterCreationWidget::ValidateAndCreateCharacter()
{
	FString CharacterName = CharacterNameInput ? CharacterNameInput->GetText().ToString().TrimStartAndEnd() : FString();

	if (CharacterName.IsEmpty())
	{
		if (ValidationText) ValidationText->SetText(FText::FromString(TEXT("Enter an operator call sign.")));
		return;
	}
	if (CharacterName.Len() > 20)
	{
		if (ValidationText) ValidationText->SetText(FText::FromString(TEXT("Call signs are limited to 20 characters.")));
		return;
	}

	if (UGameInstance* GI = GetGameInstance())
	{
		if (UCharacterProfileSubsystem* ProfileSubsystem = GI->GetSubsystem<UCharacterProfileSubsystem>())
		{
			CharacterDraft.CharacterName = CharacterName;
			CharacterDraft.AppearanceVariant = SelectedAppearance;
			CharacterDraft.SuitRole = SelectedSuitRole;
			CharacterDraft.MetaHumanPresetId = SelectedMetaHumanPresetId;
			// Keep FacePreset in sync so any code that resolves the face by preset enum
			// (rather than by MetaHumanPresetId) still reflects what the player picked here.
			CharacterDraft.FacePreset = FacePresetFromMetaHumanPresetId(SelectedMetaHumanPresetId);
			ProfileSubsystem->CreateProfileFromDraft(CharacterDraft);
		}
	}

	OnCharacterCreated.Broadcast(CharacterName, SelectedAppearance, SelectedSuitRole);
	OnCharacterCreatedWithPreset.Broadcast(
		CharacterName, SelectedAppearance, SelectedSuitRole, SelectedMetaHumanPresetId);
	RemoveFromParent();
}

void UFirstLaunchCharacterCreationWidget::OnCharacterNameChanged(const FText& Text)
{
	const int32 Length = Text.ToString().Len();
	if (CharacterCountText) CharacterCountText->SetText(FText::FromString(FString::Printf(TEXT("%d / 20"), Length)));
	if (ValidationText) ValidationText->SetText(FText::GetEmpty());
	if (ConfirmButton) ConfirmButton->SetIsEnabled(Length > 0 && Length <= 20);
}

void UFirstLaunchCharacterCreationWidget::OnBackClicked()
{
	OnBackRequested.Broadcast();
}

FReply UFirstLaunchCharacterCreationWidget::NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent)
{
	if (InKeyEvent.GetKey() == EKeys::Escape || InKeyEvent.GetKey() == EKeys::Gamepad_Special_Left || InKeyEvent.GetKey() == EKeys::Gamepad_FaceButton_Right)
	{
		OnBackClicked();
		return FReply::Handled();
	}
	return Super::NativeOnKeyDown(InGeometry, InKeyEvent);
}
