#include "UI/CharacterCreatorWidget.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/ComboBoxString.h"
#include "Components/EditableTextBox.h"
#include "Components/HorizontalBox.h"
#include "Components/Image.h"
#include "Components/SizeBox.h"
#include "Components/SafeZone.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Input/Reply.h"
#include "Kismet/KismetRenderingLibrary.h"
#include "Engine/SceneCapture2D.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Engine/TextureRenderTarget2D.h"
#include "CoopSurvivalCharacter.h"
#include "UI/MenuVisualStyle.h"

void UCharacterCreatorWidget::NativeOnInitialized()
{
	Super::NativeOnInitialized(); BuildFallbackLayout(); PopulateOptions();
	if (CharacterNameInput) CharacterNameInput->OnTextChanged.AddDynamic(this, &UCharacterCreatorWidget::OnNameChanged);
	for (UComboBoxString* Combo : {BodyCombo.Get(), FaceCombo.Get(), SkinCombo.Get(), HairCombo.Get(), VoiceCombo.Get()})
		if (Combo) Combo->OnSelectionChanged.AddDynamic(this, &UCharacterCreatorWidget::OnOptionChanged);
	if (ConfirmButton) ConfirmButton->OnClicked.AddDynamic(this, &UCharacterCreatorWidget::OnConfirmClicked);
	if (BackButton) BackButton->OnClicked.AddDynamic(this, &UCharacterCreatorWidget::OnBackClicked);
	if (RotateLeftButton) RotateLeftButton->OnClicked.AddDynamic(this, &UCharacterCreatorWidget::OnRotateLeftClicked);
	if (RotateRightButton) RotateRightButton->OnClicked.AddDynamic(this, &UCharacterCreatorWidget::OnRotateRightClicked);
	SetIsFocusable(true); if (CharacterNameInput) CharacterNameInput->SetKeyboardFocus(); RefreshDraft(); CreateCharacterPreview();
}

void UCharacterCreatorWidget::NativeConstruct()
{
	Super::NativeConstruct();
	// Focus needs the Slate tree, which exists only once the widget is constructed.
	if (CharacterNameInput) CharacterNameInput->SetKeyboardFocus();
}

void UCharacterCreatorWidget::NativeDestruct()
{
	if (CharacterNameInput) CharacterNameInput->OnTextChanged.RemoveDynamic(this, &UCharacterCreatorWidget::OnNameChanged);
	for (UComboBoxString* Combo : {BodyCombo.Get(), FaceCombo.Get(), SkinCombo.Get(), HairCombo.Get(), VoiceCombo.Get()})
		if (Combo) Combo->OnSelectionChanged.RemoveDynamic(this, &UCharacterCreatorWidget::OnOptionChanged);
	if (ConfirmButton) ConfirmButton->OnClicked.RemoveDynamic(this, &UCharacterCreatorWidget::OnConfirmClicked);
	if (BackButton) BackButton->OnClicked.RemoveDynamic(this, &UCharacterCreatorWidget::OnBackClicked);
	if (RotateLeftButton) RotateLeftButton->OnClicked.RemoveDynamic(this, &UCharacterCreatorWidget::OnRotateLeftClicked);
	if (RotateRightButton) RotateRightButton->OnClicked.RemoveDynamic(this, &UCharacterCreatorWidget::OnRotateRightClicked);
	DestroyCharacterPreview(); Super::NativeDestruct();
}

void UCharacterCreatorWidget::BuildFallbackLayout()
{
	if (!WidgetTree || WidgetTree->RootWidget) return;
	UBorder* Root = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("CharacterCreatorRoot"));
	GinnungagapMenuStyle::ApplyTerminalPanel(Root); Root->SetPadding(FMargin(90,42)); USafeZone* Safe=WidgetTree->ConstructWidget<USafeZone>(USafeZone::StaticClass(),TEXT("SafeZone"));Safe->AddChild(Root);WidgetTree->RootWidget=Safe;
	UVerticalBox* Stack = WidgetTree->ConstructWidget<UVerticalBox>(); Root->SetContent(Stack);
	auto MakeText = [this](const TCHAR* Name, const TCHAR* Copy, int32 Size, FLinearColor Color) { UTextBlock* T=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(),Name); T->SetText(FText::FromString(Copy)); T->SetFont(FSlateFontInfo(T->GetFont().FontObject,Size)); T->SetColorAndOpacity(FSlateColor(Color)); T->SetAutoWrapText(true); return T; };
	Stack->AddChildToVerticalBox(MakeText(TEXT("StepText"),TEXT("CRYO ARCHIVE  //  BIOMETRIC RECONSTRUCTION"),12,GinnungagapMenuStyle::SafetyAmber));
	UTextBlock* Heading=MakeText(TEXT("HeadingText"),TEXT("RECONSTRUCT CREW IDENTITY"),34,GinnungagapMenuStyle::CryoWhite);
	if (UVerticalBoxSlot* S=Stack->AddChildToVerticalBox(Heading)) S->SetPadding(FMargin(0,10,0,24));
	CharacterNameInput=WidgetTree->ConstructWidget<UEditableTextBox>(UEditableTextBox::StaticClass(),TEXT("CharacterNameInput")); CharacterNameInput->SetHintText(FText::FromString(TEXT("Character name"))); Stack->AddChildToVerticalBox(CharacterNameInput);
	USizeBox* PreviewSize=WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass(),TEXT("CharacterPreviewSize"));PreviewSize->SetWidthOverride(360);PreviewSize->SetHeightOverride(260);CharacterPreviewImage=WidgetTree->ConstructWidget<UImage>(UImage::StaticClass(),TEXT("CharacterPreviewImage"));PreviewSize->AddChild(CharacterPreviewImage);if(UVerticalBoxSlot* S=Stack->AddChildToVerticalBox(PreviewSize))S->SetPadding(FMargin(0,14,0,4));
	UHorizontalBox* PreviewActions=WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(),TEXT("PreviewActions"));Stack->AddChildToVerticalBox(PreviewActions);
	auto PreviewButton=[this,PreviewActions](const TCHAR* Name,const TCHAR* Copy,TObjectPtr<UButton>& Out){Out=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(),Name);GinnungagapMenuStyle::ApplyButton(Out);UTextBlock* L=WidgetTree->ConstructWidget<UTextBlock>();L->SetText(FText::FromString(Copy));Out->AddChild(L);PreviewActions->AddChildToHorizontalBox(Out);};
	PreviewButton(TEXT("RotateLeftButton"),TEXT("<  ROTATE"),RotateLeftButton);PreviewButton(TEXT("RotateRightButton"),TEXT("ROTATE  >"),RotateRightButton);
	auto AddCombo=[this,Stack,MakeText](const TCHAR* Label,const TCHAR* Name,TObjectPtr<UComboBoxString>& Out){ UTextBlock* L=MakeText(TEXT("OptionLabel"),Label,12,GinnungagapMenuStyle::SafetyAmber); if(UVerticalBoxSlot* S=Stack->AddChildToVerticalBox(L))S->SetPadding(FMargin(0,13,0,4)); Out=WidgetTree->ConstructWidget<UComboBoxString>(UComboBoxString::StaticClass(),Name); Stack->AddChildToVerticalBox(Out); };
	AddCombo(TEXT("BODY PRESET"),TEXT("BodyCombo"),BodyCombo); AddCombo(TEXT("FACE PRESET"),TEXT("FaceCombo"),FaceCombo); AddCombo(TEXT("SKIN TONE"),TEXT("SkinCombo"),SkinCombo); AddCombo(TEXT("HAIR STYLE"),TEXT("HairCombo"),HairCombo); AddCombo(TEXT("VOICE PROFILE"),TEXT("VoiceCombo"),VoiceCombo);
	SummaryText=MakeText(TEXT("SummaryText"),TEXT(""),13,GinnungagapMenuStyle::MutedSteel); if(UVerticalBoxSlot* S=Stack->AddChildToVerticalBox(SummaryText))S->SetPadding(FMargin(0,18,0,6));
	ValidationText=MakeText(TEXT("ValidationText"),TEXT("IDENTITY RECORD INCOMPLETE"),12,GinnungagapMenuStyle::FaultRed); Stack->AddChildToVerticalBox(ValidationText);
	UHorizontalBox* Actions=WidgetTree->ConstructWidget<UHorizontalBox>(); if(UVerticalBoxSlot* S=Stack->AddChildToVerticalBox(Actions))S->SetPadding(FMargin(0,20,0,0));
	auto AddButton=[this,Actions](const TCHAR* Name,const TCHAR* Copy,TObjectPtr<UButton>& Out){Out=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(),Name);GinnungagapMenuStyle::ApplyButton(Out,FString(Name).Contains(TEXT("Confirm")));UTextBlock* L=WidgetTree->ConstructWidget<UTextBlock>();L->SetText(FText::FromString(Copy));Out->AddChild(L);Actions->AddChildToHorizontalBox(Out);};
	AddButton(TEXT("BackButton"),TEXT("<  BACK"),BackButton); AddButton(TEXT("ConfirmButton"),TEXT("SAVE CHARACTER  >"),ConfirmButton); ConfirmButton->SetIsEnabled(false);
}

void UCharacterCreatorWidget::PopulateOptions()
{
	auto Fill=[](UComboBoxString* Combo,const TArray<FString>& Values,int32 Selected){if(!Combo)return;for(const FString& V:Values)Combo->AddOption(V);Combo->SetSelectedIndex(Selected);};
	Fill(BodyCombo,{TEXT("Light"),TEXT("Average"),TEXT("Broad"),TEXT("Heavy")},1); Fill(FaceCombo,{TEXT("Face 01"),TEXT("Face 02"),TEXT("Face 03"),TEXT("Face 04"),TEXT("Face 05"),TEXT("Face 06"),TEXT("Face 07"),TEXT("Face 08"),TEXT("Face 09"),TEXT("Face 10"),TEXT("Face 11"),TEXT("Face 12")},0);
	Fill(SkinCombo,{TEXT("Tone 01"),TEXT("Tone 02"),TEXT("Tone 03"),TEXT("Tone 04"),TEXT("Tone 05"),TEXT("Tone 06"),TEXT("Tone 07"),TEXT("Tone 08")},3); Fill(HairCombo,{TEXT("Shaved"),TEXT("Short"),TEXT("Medium"),TEXT("Long"),TEXT("Braided"),TEXT("Covered")},1); Fill(VoiceCombo,{TEXT("Voice 01"),TEXT("Voice 02"),TEXT("Voice 03"),TEXT("Voice 04")},0);
}

void UCharacterCreatorWidget::RefreshDraft()
{
	Draft.BodyPreset=static_cast<ECharacterBodyPreset>(FMath::Max(0,BodyCombo?BodyCombo->GetSelectedIndex():1)); Draft.FacePreset=static_cast<ECharacterFacePreset>(FMath::Max(0,FaceCombo?FaceCombo->GetSelectedIndex():0)); Draft.SkinTone=static_cast<ECharacterSkinTone>(FMath::Max(0,SkinCombo?SkinCombo->GetSelectedIndex():3)); Draft.HairStyle=static_cast<ECharacterHairStyle>(FMath::Max(0,HairCombo?HairCombo->GetSelectedIndex():1)); Draft.VoiceProfile=static_cast<ECharacterVoiceProfile>(FMath::Max(0,VoiceCombo?VoiceCombo->GetSelectedIndex():0));
	// Keep MetaHumanPresetId in sync so any code that resolves the assembled face by preset ID
	// (rather than by FacePreset) still reflects what the player picked here.
	Draft.MetaHumanPresetId=MetaHumanPresetIdFromFacePreset(Draft.FacePreset);
	if(SummaryText)SummaryText->SetText(FText::FromString(FString::Printf(TEXT("%s  //  %s  //  %s  //  %s  //  %s"),*BodyCombo->GetSelectedOption().ToUpper(),*FaceCombo->GetSelectedOption().ToUpper(),*SkinCombo->GetSelectedOption().ToUpper(),*HairCombo->GetSelectedOption().ToUpper(),*VoiceCombo->GetSelectedOption().ToUpper())));
	RefreshCharacterPreview();
}

void UCharacterCreatorWidget::CreateCharacterPreview()
{
	if(!CharacterPreviewImage||!GetWorld())return;
	PreviewRenderTarget=UKismetRenderingLibrary::CreateRenderTarget2D(this,512,512,ETextureRenderTargetFormat::RTF_RGBA8,FLinearColor(0.008f,0.012f,0.018f,1));
	if(!PreviewRenderTarget)return;CharacterPreviewImage->SetBrushResourceObject(PreviewRenderTarget);
	const FVector Origin(0,0,-120000);PreviewCharacter=GetWorld()->SpawnActor<ACoopSurvivalCharacter>(ACoopSurvivalCharacter::StaticClass(),Origin,FRotator::ZeroRotator);PreviewCapture=GetWorld()->SpawnActor<ASceneCapture2D>(Origin+FVector(390,0,70),FRotator(0,180,0));
	if(!PreviewCharacter||!PreviewCapture)return;PreviewCharacter->SetReplicates(false);PreviewCharacter->SetActorEnableCollision(false);PreviewCharacter->SetCharacterCreatorPreviewMode(true);
	USceneCaptureComponent2D* Capture=PreviewCapture->GetCaptureComponent2D();Capture->TextureTarget=PreviewRenderTarget;Capture->CaptureSource=ESceneCaptureSource::SCS_FinalColorLDR;Capture->FOVAngle=36;Capture->bCaptureEveryFrame=false;Capture->bCaptureOnMovement=false;Capture->ShowOnlyActorComponents(PreviewCharacter);RefreshCharacterPreview();
}

void UCharacterCreatorWidget::RefreshCharacterPreview()
{
	if(PreviewCharacter)PreviewCharacter->ApplyCharacterIdentity(Draft);if(PreviewCapture)PreviewCapture->GetCaptureComponent2D()->CaptureScene();
}

void UCharacterCreatorWidget::DestroyCharacterPreview()
{
	if(PreviewCapture)PreviewCapture->Destroy();if(PreviewCharacter)PreviewCharacter->Destroy();PreviewCapture=nullptr;PreviewCharacter=nullptr;PreviewRenderTarget=nullptr;
}

void UCharacterCreatorWidget::OnRotateLeftClicked(){if(PreviewCharacter)PreviewCharacter->AddActorLocalRotation(FRotator(0,-20,0));RefreshCharacterPreview();}
void UCharacterCreatorWidget::OnRotateRightClicked(){if(PreviewCharacter)PreviewCharacter->AddActorLocalRotation(FRotator(0,20,0));RefreshCharacterPreview();}

void UCharacterCreatorWidget::OnNameChanged(const FText& Text){Draft.CharacterName=Text.ToString().TrimStartAndEnd();const bool Valid=!Draft.CharacterName.IsEmpty()&&Draft.CharacterName.Len()<=20;if(ConfirmButton)ConfirmButton->SetIsEnabled(Valid);if(ValidationText)ValidationText->SetText(Valid?FText::GetEmpty():FText::FromString(TEXT("NAME REQUIRED // 20 CHARACTER MAXIMUM")));}
void UCharacterCreatorWidget::OnOptionChanged(FString Item,ESelectInfo::Type SelectionType){RefreshDraft();}
void UCharacterCreatorWidget::OnConfirmClicked(){if(!Draft.CharacterName.IsEmpty())OnIdentityConfirmed.Broadcast(Draft);}
void UCharacterCreatorWidget::OnBackClicked(){OnBackRequested.Broadcast();}
FReply UCharacterCreatorWidget::NativeOnKeyDown(const FGeometry& G,const FKeyEvent& E){if(E.GetKey()==EKeys::Escape||E.GetKey()==EKeys::Gamepad_FaceButton_Right){OnBackClicked();return FReply::Handled();}return Super::NativeOnKeyDown(G,E);}
