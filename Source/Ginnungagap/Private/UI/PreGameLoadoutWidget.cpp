#include "UI/PreGameLoadoutWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/SizeBox.h"
#include "Components/Spacer.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Equipment/ExpeditionLoadoutSubsystem.h"
#include "Engine/GameInstance.h"
#include "Input/Reply.h"
#include "Meta/CharacterProfileSubsystem.h"
#include "UI/SkillPayloadPickerWidget.h"
#include "UI/SkillTreeWidget.h"
#include "UI/MenuWidgetResolution.h"

void UPreGameLoadoutWidget::NativeOnInitialized()
{
	Super::NativeOnInitialized();
	BuildFallbackLayout();
	if (UGameInstance* GI = GetGameInstance()) LoadoutSubsystem = GI->GetSubsystem<UExpeditionLoadoutSubsystem>();

	if (HelmetVisorButton) HelmetVisorButton->OnClicked.AddDynamic(this, &UPreGameLoadoutWidget::OnHelmetVisorClicked);
	if (ThermalPlatingButton) ThermalPlatingButton->OnClicked.AddDynamic(this, &UPreGameLoadoutWidget::OnThermalPlatingClicked);
	if (RadiationShieldButton) RadiationShieldButton->OnClicked.AddDynamic(this, &UPreGameLoadoutWidget::OnRadiationShieldClicked);
	if (PressureSealButton) PressureSealButton->OnClicked.AddDynamic(this, &UPreGameLoadoutWidget::OnPressureSealClicked);
	if (ArmorPlatingButton) ArmorPlatingButton->OnClicked.AddDynamic(this, &UPreGameLoadoutWidget::OnArmorPlatingClicked);
	if (OxygenFilterButton) OxygenFilterButton->OnClicked.AddDynamic(this, &UPreGameLoadoutWidget::OnOxygenFilterClicked);
	if (BackButton) BackButton->OnClicked.AddDynamic(this, &UPreGameLoadoutWidget::OnBackClicked);
	if (DeployButton) DeployButton->OnClicked.AddDynamic(this, &UPreGameLoadoutWidget::OnDeployClicked);

	if (UGameInstance* GI = GetGameInstance())
	{
		if (const UCharacterProfileSubsystem* Profile = GI->GetSubsystem<UCharacterProfileSubsystem>())
		{
			if (OperatorText) OperatorText->SetText(FText::FromString(Profile->GetCharacterName().ToUpper()));
			if (RoleText)
			{
				const UEnum* RoleEnum = StaticEnum<EPressureSuitRole>();
				RoleText->SetText(FText::Format(NSLOCTEXT("PreGame", "RoleFormat", "{0} PRESSURE SUIT"),
					RoleEnum ? RoleEnum->GetDisplayNameTextByValue(static_cast<int64>(Profile->GetSuitRole())) : FText::GetEmpty()));
			}
		}
	}
	RefreshEquipmentDisplay();
	SetIsFocusable(true);
	if (HelmetVisorButton) HelmetVisorButton->SetKeyboardFocus();
}

void UPreGameLoadoutWidget::NativeConstruct()
{
	Super::NativeConstruct();
	// Focus needs the Slate tree, which exists only once the widget is constructed.
	if (HelmetVisorButton) HelmetVisorButton->SetKeyboardFocus();
}

void UPreGameLoadoutWidget::NativeDestruct()
{
	if (HelmetVisorButton) HelmetVisorButton->OnClicked.RemoveDynamic(this, &UPreGameLoadoutWidget::OnHelmetVisorClicked);
	if (ThermalPlatingButton) ThermalPlatingButton->OnClicked.RemoveDynamic(this, &UPreGameLoadoutWidget::OnThermalPlatingClicked);
	if (RadiationShieldButton) RadiationShieldButton->OnClicked.RemoveDynamic(this, &UPreGameLoadoutWidget::OnRadiationShieldClicked);
	if (PressureSealButton) PressureSealButton->OnClicked.RemoveDynamic(this, &UPreGameLoadoutWidget::OnPressureSealClicked);
	if (ArmorPlatingButton) ArmorPlatingButton->OnClicked.RemoveDynamic(this, &UPreGameLoadoutWidget::OnArmorPlatingClicked);
	if (OxygenFilterButton) OxygenFilterButton->OnClicked.RemoveDynamic(this, &UPreGameLoadoutWidget::OnOxygenFilterClicked);
	if (BackButton) BackButton->OnClicked.RemoveDynamic(this, &UPreGameLoadoutWidget::OnBackClicked);
	if (DeployButton) DeployButton->OnClicked.RemoveDynamic(this, &UPreGameLoadoutWidget::OnDeployClicked);
	Super::NativeDestruct();
}

void UPreGameLoadoutWidget::BuildFallbackLayout()
{
	if (!WidgetTree || WidgetTree->RootWidget) return;
	UBorder* Background = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("PreGameBackground"));
	Background->SetBrushColor(FLinearColor(0.006f, 0.012f, 0.018f, 1.0f)); Background->SetPadding(FMargin(54.0f, 34.0f));
	WidgetTree->RootWidget = Background;
	UVerticalBox* Root = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("PreGameRoot")); Background->SetContent(Root);
	auto Text = [this](const TCHAR* Name, const TCHAR* Copy, int32 Size, FLinearColor Color)
	{
		UTextBlock* Result = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), Name);
		Result->SetText(FText::FromString(Copy)); Result->SetFont(FSlateFontInfo(Result->GetFont().FontObject, Size));
		Result->SetColorAndOpacity(FSlateColor(Color)); return Result;
	};

	UHorizontalBox* Eyebrow = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("EyebrowRow"));
	Eyebrow->AddChildToHorizontalBox(Text(TEXT("StepText"), TEXT("EXPEDITION SETUP  //  03 OF 03"), 11, FLinearColor(0.30f, 0.86f, 1.0f)));
	USpacer* EyebrowSpace = WidgetTree->ConstructWidget<USpacer>(USpacer::StaticClass());
	if (UHorizontalBoxSlot* SpaceSlot = Eyebrow->AddChildToHorizontalBox(EyebrowSpace)) SpaceSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	RoleText = Text(TEXT("RoleText"), TEXT("STANDARD CREW PRESSURE SUIT"), 11, FLinearColor(0.48f, 0.58f, 0.62f)); Eyebrow->AddChildToHorizontalBox(RoleText);
	Root->AddChildToVerticalBox(Eyebrow);

	UHorizontalBox* TitleRow = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("TitleRow"));
	TitleRow->AddChildToHorizontalBox(Text(TEXT("HeadingText"), TEXT("FINALIZE EXPEDITION KIT"), 31, FLinearColor(0.88f, 0.94f, 0.95f)));
	USpacer* TitleSpace = WidgetTree->ConstructWidget<USpacer>(USpacer::StaticClass());
	if (UHorizontalBoxSlot* TitleSpaceSlot = TitleRow->AddChildToHorizontalBox(TitleSpace)) TitleSpaceSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	OperatorText = Text(TEXT("OperatorText"), TEXT("OPERATOR"), 17, FLinearColor(0.88f, 0.94f, 0.95f)); TitleRow->AddChildToHorizontalBox(OperatorText);
	if (UVerticalBoxSlot* TitleSlot = Root->AddChildToVerticalBox(TitleRow)) TitleSlot->SetPadding(FMargin(0, 8, 0, 22));

	UHorizontalBox* Content = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("LoadoutContent"));
	if (UVerticalBoxSlot* ContentSlot = Root->AddChildToVerticalBox(Content)) ContentSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	USizeBox* EquipmentWidth = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass(), TEXT("EquipmentWidth")); EquipmentWidth->SetWidthOverride(570.0f);
	UBorder* EquipmentPanel = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("EquipmentPanel"));
	EquipmentPanel->SetBrushColor(FLinearColor(0.012f, 0.027f, 0.035f, 0.98f)); EquipmentPanel->SetPadding(FMargin(22.0f)); EquipmentWidth->AddChild(EquipmentPanel);
	if (UHorizontalBoxSlot* EquipmentSlot = Content->AddChildToHorizontalBox(EquipmentWidth)) EquipmentSlot->SetPadding(FMargin(0, 0, 16, 0));
	UVerticalBox* EquipmentStack = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("EquipmentStack")); EquipmentPanel->SetContent(EquipmentStack);
	EquipmentStack->AddChildToVerticalBox(Text(TEXT("EquipmentHeading"), TEXT("QUARTERMASTER // EQUIPMENT"), 20, FLinearColor(0.88f, 0.94f, 0.95f)));
	SupplyText = Text(TEXT("SupplyText"), TEXT("SUPPLY  0 / 8"), 12, FLinearColor(0.82f, 0.66f, 0.30f));
	if (UVerticalBoxSlot* SupplySlot = EquipmentStack->AddChildToVerticalBox(SupplyText)) SupplySlot->SetPadding(FMargin(0, 6, 0, 13));
	auto AddEquipment = [this, EquipmentStack, Text](const TCHAR* Name, const TCHAR* Label, const TCHAR* Detail, TObjectPtr<UButton>& Button)
	{
		Button = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), Name); Button->SetBackgroundColor(FLinearColor(0.03f, 0.08f, 0.10f, 1.0f));
		UVerticalBox* Copy = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
		Copy->AddChildToVerticalBox(Text(*FString(Name).Append(TEXT("Label")), Label, 14, FLinearColor(0.88f, 0.94f, 0.95f)));
		UTextBlock* DetailText = Text(*FString(Name).Append(TEXT("Detail")), Detail, 10, FLinearColor(0.48f, 0.58f, 0.62f)); DetailText->SetAutoWrapText(true);
		Copy->AddChildToVerticalBox(DetailText); Button->AddChild(Copy);
		if (UVerticalBoxSlot* Slot = EquipmentStack->AddChildToVerticalBox(Button)) Slot->SetPadding(FMargin(0, 0, 0, 6));
	};
	AddEquipment(TEXT("HelmetVisorButton"), TEXT("SURVEY VISOR  //  HEAD  //  1 SUP"), TEXT("Fault and particulate detection."), HelmetVisorButton);
	AddEquipment(TEXT("ThermalPlatingButton"), TEXT("THERMAL PLATING  //  CHEST  //  3 SUP"), TEXT("Heat protection; replaces impact carapace."), ThermalPlatingButton);
	AddEquipment(TEXT("RadiationShieldButton"), TEXT("RAD-SHIELD BRACERS  //  ARMS  //  2 SUP"), TEXT("Reactor-work radiation protection."), RadiationShieldButton);
	AddEquipment(TEXT("PressureSealButton"), TEXT("PRESSURE SEAL KIT  //  LEGS  //  1 SUP"), TEXT("Emergency decompression protection."), PressureSealButton);
	AddEquipment(TEXT("ArmorPlatingButton"), TEXT("IMPACT CARAPACE  //  CHEST  //  3 SUP"), TEXT("Integrity protection; replaces thermal plating."), ArmorPlatingButton);
	AddEquipment(TEXT("OxygenFilterButton"), TEXT("SCRUBBER PACK  //  ACCESSORY  //  2 SUP"), TEXT("Dust and contaminated-atmosphere filtration."), OxygenFilterButton);
	StatsText = Text(TEXT("StatsText"), TEXT("LOADOUT EFFECTS"), 10, FLinearColor(0.58f, 0.70f, 0.72f)); StatsText->SetAutoWrapText(true);
	if (UVerticalBoxSlot* StatsSlot = EquipmentStack->AddChildToVerticalBox(StatsText)) StatsSlot->SetPadding(FMargin(0, 9, 0, 0));

	TSubclassOf<USkillTreeWidget> ResolvedSkillTreeClass = SkillTreeWidgetClass;
	if (!ResolvedSkillTreeClass)
	{
		ResolvedSkillTreeClass = GinnungagapMenuWidgets::ResolveClass<USkillTreeWidget>(
			GINNUNGAGAP_MENU_WBP("SkillTree"));
	}
	SkillTreeWidget = CreateWidget<USkillTreeWidget>(GetOwningPlayer(), ResolvedSkillTreeClass, TEXT("SkillTreeWidget"));
	if (SkillTreeWidget)
	{
		if (UHorizontalBoxSlot* SkillSlot = Content->AddChildToHorizontalBox(SkillTreeWidget)) SkillSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	}

	// Payload sits beside the tree rather than inside it. Buying a procedure and deciding to carry
	// it are separate choices, and a player rebuilding a loadout should not have to scroll a
	// purchase screen to do it.
	TSubclassOf<USkillPayloadPickerWidget> ResolvedPayloadClass = PayloadPickerWidgetClass;
	if (!ResolvedPayloadClass)
	{
		ResolvedPayloadClass = GinnungagapMenuWidgets::ResolveClass<USkillPayloadPickerWidget>(
			GINNUNGAGAP_MENU_WBP("SkillPayloadPicker"));
	}
	PayloadPickerWidget = CreateWidget<USkillPayloadPickerWidget>(GetOwningPlayer(), ResolvedPayloadClass, TEXT("PayloadPickerWidget"));
	if (PayloadPickerWidget)
	{
		if (UHorizontalBoxSlot* PayloadSlot = Content->AddChildToHorizontalBox(PayloadPickerWidget)) PayloadSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	}

	UHorizontalBox* Footer = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("Footer"));
	auto AddFooterButton = [this, Footer, Text](const TCHAR* Name, const TCHAR* Label, TObjectPtr<UButton>& Button, FLinearColor Color)
	{
		Button = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), Name); Button->SetBackgroundColor(Color);
		Button->AddChild(Text(*FString(Name).Append(TEXT("Label")), Label, 13, FLinearColor(0.88f, 0.94f, 0.95f))); Footer->AddChildToHorizontalBox(Button);
	};
	AddFooterButton(TEXT("BackButton"), TEXT("<  MISSION PARAMETERS"), BackButton, FLinearColor(0.03f, 0.08f, 0.10f, 1.0f));
	StatusText = Text(TEXT("StatusText"), TEXT("SELECT KIT  //  UNLOCK CERTIFICATIONS  //  DEPLOY"), 10, FLinearColor(0.48f, 0.58f, 0.62f));
	if (UHorizontalBoxSlot* StatusSlot = Footer->AddChildToHorizontalBox(StatusText)) { StatusSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); StatusSlot->SetHorizontalAlignment(HAlign_Center); StatusSlot->SetVerticalAlignment(VAlign_Center); }
	AddFooterButton(TEXT("DeployButton"), TEXT("DEPLOY EXPEDITION  >"), DeployButton, FLinearColor(0.04f, 0.35f, 0.39f, 1.0f));
	if (UVerticalBoxSlot* FooterSlot = Root->AddChildToVerticalBox(Footer)) FooterSlot->SetPadding(FMargin(0, 16, 0, 0));
}

void UPreGameLoadoutWidget::ToggleEquipment(uint8 EquipmentTypeValue)
{
	if (!LoadoutSubsystem) return;
	if (!LoadoutSubsystem->ToggleEquipment(static_cast<EEquipmentType>(EquipmentTypeValue)))
	{
		if (StatusText) StatusText->SetText(FText::FromString(TEXT("SUPPLY BUDGET EXCEEDED  //  REMOVE OR REPLACE KIT")));
	}
	else if (StatusText) StatusText->SetText(FText::FromString(TEXT("LOADOUT UPDATED")));
	RefreshEquipmentDisplay();
}

void UPreGameLoadoutWidget::RefreshEquipmentDisplay()
{
	if (!LoadoutSubsystem) return;
	if (SupplyText) SupplyText->SetText(FText::FromString(FString::Printf(TEXT("SUPPLY  %d / %d  //  %d REMAINING"),
		LoadoutSubsystem->GetUsedSupply(), LoadoutSubsystem->SupplyBudget, LoadoutSubsystem->GetRemainingSupply())));
	StyleEquipmentButton(HelmetVisorButton, static_cast<uint8>(EEquipmentType::HelmetVisor));
	StyleEquipmentButton(ThermalPlatingButton, static_cast<uint8>(EEquipmentType::ThermalPlating));
	StyleEquipmentButton(RadiationShieldButton, static_cast<uint8>(EEquipmentType::RadiationShield));
	StyleEquipmentButton(PressureSealButton, static_cast<uint8>(EEquipmentType::PressureSeal));
	StyleEquipmentButton(ArmorPlatingButton, static_cast<uint8>(EEquipmentType::ArmorPlating));
	StyleEquipmentButton(OxygenFilterButton, static_cast<uint8>(EEquipmentType::OxygenFilter));
	const FEquipmentStats Stats = LoadoutSubsystem->GetSelectedStats();
	if (StatsText) StatsText->SetText(FText::FromString(FString::Printf(
		TEXT("LOADOUT EFFECTS  //  RAD %.0f%%  HEAT +%.0fC  PRESSURE +%.0f kPa  INTEGRITY +%.0f%%  MOBILITY %+.0f%%  DUST %.0f%%"),
		Stats.RadiationResistance, Stats.ThermalResistance, Stats.PressureResistance,
		Stats.SuitIntegrityBonus, Stats.MovementSpeedBonus, Stats.DustProtection)));
}

void UPreGameLoadoutWidget::StyleEquipmentButton(UButton* Button, uint8 EquipmentTypeValue) const
{
	if (!Button || !LoadoutSubsystem) return;
	const bool bSelected = LoadoutSubsystem->IsEquipmentSelected(static_cast<EEquipmentType>(EquipmentTypeValue));
	Button->SetBackgroundColor(bSelected ? FLinearColor(0.04f, 0.30f, 0.34f, 1.0f) : FLinearColor(0.03f, 0.08f, 0.10f, 1.0f));
	Button->SetToolTipText(FText::FromString(bSelected ? TEXT("Equipped — activate to remove") : TEXT("Activate to equip")));
}

void UPreGameLoadoutWidget::OnHelmetVisorClicked() { ToggleEquipment(static_cast<uint8>(EEquipmentType::HelmetVisor)); }
void UPreGameLoadoutWidget::OnThermalPlatingClicked() { ToggleEquipment(static_cast<uint8>(EEquipmentType::ThermalPlating)); }
void UPreGameLoadoutWidget::OnRadiationShieldClicked() { ToggleEquipment(static_cast<uint8>(EEquipmentType::RadiationShield)); }
void UPreGameLoadoutWidget::OnPressureSealClicked() { ToggleEquipment(static_cast<uint8>(EEquipmentType::PressureSeal)); }
void UPreGameLoadoutWidget::OnArmorPlatingClicked() { ToggleEquipment(static_cast<uint8>(EEquipmentType::ArmorPlating)); }
void UPreGameLoadoutWidget::OnOxygenFilterClicked() { ToggleEquipment(static_cast<uint8>(EEquipmentType::OxygenFilter)); }
void UPreGameLoadoutWidget::OnBackClicked() { OnBackRequested.Broadcast(); }
void UPreGameLoadoutWidget::OnDeployClicked() { OnDeployRequested.Broadcast(); }

FReply UPreGameLoadoutWidget::NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent)
{
	const FKey Key = InKeyEvent.GetKey();
	if (Key == EKeys::Escape || Key == EKeys::Gamepad_Special_Left || Key == EKeys::Gamepad_FaceButton_Right)
	{
		OnBackClicked(); return FReply::Handled();
	}
	return Super::NativeOnKeyDown(InGeometry, InKeyEvent);
}
