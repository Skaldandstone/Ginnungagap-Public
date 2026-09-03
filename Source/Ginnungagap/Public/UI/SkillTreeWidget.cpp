#include "UI/SkillTreeWidget.h"
#include "UI/SkillEntryWidget.h"
#include "Progression/ClassSkillTreeSubsystem.h"
#include "Meta/RunOutcomeSubsystem.h"
#include "Engine/GameInstance.h"
#include "Components/VerticalBox.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/ScrollBoxSlot.h"
#include "Components/Spacer.h"
#include "Components/VerticalBoxSlot.h"

void USkillTreeWidget::NativeConstruct()
{
	Super::NativeConstruct();
	BuildFallbackLayout();

	if (UGameInstance* GI = GetGameInstance())
	{
		SkillTreeSubsystem = GI->GetSubsystem<UClassSkillTreeSubsystem>();
		RunOutcomeSubsystem = GI->GetSubsystem<URunOutcomeSubsystem>();
	}
	if (!SkillEntryWidgetClass) SkillEntryWidgetClass = USkillEntryWidget::StaticClass();
	if (RunOutcomeSubsystem) CurrentSelectedRole = RunOutcomeSubsystem->GetPlayerRole();

	// Bind class selection buttons
	if (SecurityButton)
	{
		SecurityButton->OnClicked.AddDynamic(this, &USkillTreeWidget::OnSecurityClicked);
	}
	if (CrewButton)
	{
		CrewButton->OnClicked.AddDynamic(this, &USkillTreeWidget::OnCrewClicked);
	}
	if (EngineeringButton)
	{
		EngineeringButton->OnClicked.AddDynamic(this, &USkillTreeWidget::OnEngineeringClicked);
	}
	if (MedicalButton)
	{
		MedicalButton->OnClicked.AddDynamic(this, &USkillTreeWidget::OnMedicalClicked);
	}

	RefreshSkillTree();
}

void USkillTreeWidget::NativeDestruct()
{
	if (SecurityButton) SecurityButton->OnClicked.RemoveDynamic(this, &USkillTreeWidget::OnSecurityClicked);
	if (CrewButton) CrewButton->OnClicked.RemoveDynamic(this, &USkillTreeWidget::OnCrewClicked);
	if (EngineeringButton) EngineeringButton->OnClicked.RemoveDynamic(this, &USkillTreeWidget::OnEngineeringClicked);
	if (MedicalButton) MedicalButton->OnClicked.RemoveDynamic(this, &USkillTreeWidget::OnMedicalClicked);
	Super::NativeDestruct();
}

void USkillTreeWidget::BuildFallbackLayout()
{
	if (!WidgetTree || WidgetTree->RootWidget) return;
	UBorder* Root = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("SkillTreeRoot"));
	Root->SetBrushColor(FLinearColor(0.012f, 0.027f, 0.035f, 0.98f)); Root->SetPadding(FMargin(22.0f));
	WidgetTree->RootWidget = Root;
	UVerticalBox* Stack = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("SkillTreeStack")); Root->SetContent(Stack);
	auto Text = [this](const TCHAR* Name, const TCHAR* Copy, int32 Size, FLinearColor Color)
	{
		UTextBlock* Result = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), Name);
		Result->SetText(FText::FromString(Copy)); Result->SetFont(FSlateFontInfo(Result->GetFont().FontObject, Size));
		Result->SetColorAndOpacity(FSlateColor(Color)); return Result;
	};
	UHorizontalBox* Header = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("SkillHeader"));
	RoleNameText = Text(TEXT("RoleNameText"), TEXT("CREW DISCIPLINE"), 21, FLinearColor(0.88f, 0.94f, 0.95f));
	Header->AddChildToHorizontalBox(RoleNameText);
	USpacer* HeaderSpace = WidgetTree->ConstructWidget<USpacer>(USpacer::StaticClass());
	if (UHorizontalBoxSlot* SpaceSlot = Header->AddChildToHorizontalBox(HeaderSpace)) SpaceSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	PointsText = Text(TEXT("PointsText"), TEXT("0 SP"), 12, FLinearColor(0.30f, 0.86f, 1.0f));
	CurrencyText = Text(TEXT("CurrencyText"), TEXT("0 CR"), 12, FLinearColor(0.82f, 0.66f, 0.30f));
	if (UHorizontalBoxSlot* PointsSlot = Header->AddChildToHorizontalBox(PointsText)) PointsSlot->SetPadding(FMargin(0, 0, 18, 0));
	Header->AddChildToHorizontalBox(CurrencyText); Stack->AddChildToVerticalBox(Header);

	UHorizontalBox* Tabs = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("ClassTabs"));
	auto AddTab = [this, Tabs, Text](const TCHAR* Name, const TCHAR* Label, UButton*& Button)
	{
		Button = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), Name); Button->SetBackgroundColor(FLinearColor(0.03f, 0.08f, 0.10f, 1.0f));
		const FString LabelName = FString(Name) + TEXT("Label");
		Button->AddChild(Text(*LabelName, Label, 11, FLinearColor(0.67f, 0.75f, 0.77f)));
		if (UHorizontalBoxSlot* Slot = Tabs->AddChildToHorizontalBox(Button)) { Slot->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); Slot->SetPadding(FMargin(0, 0, 6, 0)); }
	};
	AddTab(TEXT("CrewButton"), TEXT("CREW"), CrewButton);
	AddTab(TEXT("EngineeringButton"), TEXT("ENGINEERING"), EngineeringButton);
	AddTab(TEXT("MedicalButton"), TEXT("MEDICAL"), MedicalButton);
	AddTab(TEXT("SecurityButton"), TEXT("SECURITY"), SecurityButton);
	if (UVerticalBoxSlot* TabsSlot = Stack->AddChildToVerticalBox(Tabs)) TabsSlot->SetPadding(FMargin(0, 18, 0, 14));

	SkillScrollBox = WidgetTree->ConstructWidget<UScrollBox>(UScrollBox::StaticClass(), TEXT("SkillScrollBox"));
	SkillScrollBox->SetScrollBarVisibility(ESlateVisibility::Visible);
	if (UVerticalBoxSlot* ScrollSlot = Stack->AddChildToVerticalBox(SkillScrollBox)) ScrollSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
}

void USkillTreeWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);

	// Periodically update points display in case it changes externally
	PointsRefreshTimer += InDeltaTime;
	if (PointsRefreshTimer >= 1.0f)
	{
		UpdatePointsDisplay();
		PointsRefreshTimer = 0.0f;
	}
}

void USkillTreeWidget::RefreshSkillTree()
{
	SelectRole(CurrentSelectedRole);
}

void USkillTreeWidget::SelectRole(EPressureSuitRole SelectedClass)
{
	CurrentSelectedRole = SelectedClass;
	if (RunOutcomeSubsystem) RunOutcomeSubsystem->SetPlayerRole(SelectedClass);
	UpdateRoleDisplay();
	PopulateSkillsForRole();
	UpdatePointsDisplay();
	RefreshRoleTabStyles();
}

void USkillTreeWidget::UpdateRoleDisplay()
{
	if (!RoleNameText)
		return;

	// Read straight off the enum's own display name rather than a switch that restates it.
	//
	// The switch this replaces carried a comment promising the tree could not drift out of step
	// with the role, and then drifted: it still said "Crew" after the role became Science, so the
	// header lied to the player about which discipline they were looking at. A second list of the
	// same names is a second thing to forget to update, which is exactly what happened.
	FString RoleName = StaticEnum<EPressureSuitRole>()
		->GetDisplayNameTextByValue(static_cast<int64>(CurrentSelectedRole)).ToString();

	RoleNameText->SetText(FText::FromString(RoleName.ToUpper() + TEXT(" DISCIPLINE")));
}

void USkillTreeWidget::RefreshRoleTabStyles()
{
	auto Style = [this](UButton* Button, EPressureSuitRole Class)
	{
		if (Button) Button->SetBackgroundColor(Class == CurrentSelectedRole
			? FLinearColor(0.05f, 0.31f, 0.36f, 1.0f) : FLinearColor(0.03f, 0.08f, 0.10f, 1.0f));
	};
	Style(CrewButton, EPressureSuitRole::Scientist); Style(EngineeringButton, EPressureSuitRole::Engineering);
	Style(MedicalButton, EPressureSuitRole::Medical); Style(SecurityButton, EPressureSuitRole::Security);
}

void USkillTreeWidget::UpdatePointsDisplay()
{
	if (!RunOutcomeSubsystem)
		return;

	int32 AvailablePoints = RunOutcomeSubsystem->GetRoleSkillPoints(CurrentSelectedRole);
	int32 BankedCurrency = RunOutcomeSubsystem->TotalBankedCurrency;

	if (PointsText)
	{
		PointsText->SetText(FText::FromString(FString::Printf(TEXT("%d SP"), AvailablePoints)));
	}

	if (CurrencyText)
	{
		CurrencyText->SetText(FText::FromString(FString::Printf(TEXT("%d CR"), BankedCurrency)));
	}
}

void USkillTreeWidget::PopulateSkillsForRole()
{
	if (!SkillScrollBox || !SkillTreeSubsystem || !RunOutcomeSubsystem || !SkillEntryWidgetClass)
	{
		return;
	}

	SkillScrollBox->ClearChildren();

	// Get all skills for the selected class
	TArray<FClassSkill> ClassSkills = SkillTreeSubsystem->GetAllSkillsForRole(CurrentSelectedRole);

	// Organize by tier
	TMap<int32, TArray<FClassSkill>> SkillsByTier;
	for (const FClassSkill& Skill : ClassSkills)
	{
		if (!SkillsByTier.Contains(Skill.Tier))
		{
			SkillsByTier.Add(Skill.Tier, TArray<FClassSkill>());
		}
		SkillsByTier[Skill.Tier].Add(Skill);
	}

	// Sort tiers
	TArray<int32> Tiers;
	SkillsByTier.GetKeys(Tiers);
	Tiers.Sort();

	int32 AvailablePoints = RunOutcomeSubsystem->GetRoleSkillPoints(CurrentSelectedRole);
	int32 BankedCurrency = RunOutcomeSubsystem->TotalBankedCurrency;
	const FClassSkillsArray OwnedSkills = RunOutcomeSubsystem->GetRoleSkills(CurrentSelectedRole);

	// Create widgets for each tier
	for (int32 Tier : Tiers)
	{
		// Add tier header
		UTextBlock* TierHeader = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
		TierHeader->SetText(FText::FromString(FString::Printf(TEXT("TIER %02d  //  CERTIFICATION"), Tier)));
		TierHeader->SetFont(FSlateFontInfo(TierHeader->GetFont().FontObject, 10));
		TierHeader->SetColorAndOpacity(FSlateColor(FLinearColor(0.30f, 0.86f, 1.0f)));
		if (UScrollBoxSlot* TierSlot = Cast<UScrollBoxSlot>(SkillScrollBox->AddChild(TierHeader))) TierSlot->SetPadding(FMargin(0, 12, 0, 6));

		// Add skills for this tier
		for (const FClassSkill& Skill : SkillsByTier[Tier])
		{
			USkillEntryWidget* SkillEntry = CreateWidget<USkillEntryWidget>(this, SkillEntryWidgetClass);
			if (SkillEntry)
			{
				SkillEntry->SetSkillData(Skill, CurrentSelectedRole, OwnedSkills, AvailablePoints, BankedCurrency);
				SkillEntry->OnSkillUnlocked.AddDynamic(this, &USkillTreeWidget::OnSkillUnlocked);
				if (UScrollBoxSlot* EntrySlot = Cast<UScrollBoxSlot>(SkillScrollBox->AddChild(SkillEntry))) EntrySlot->SetPadding(FMargin(0, 0, 0, 7));
			}
		}
	}
}

void USkillTreeWidget::OnSecurityClicked()
{
	SelectRole(EPressureSuitRole::Security);
}

void USkillTreeWidget::OnCrewClicked()
{
	SelectRole(EPressureSuitRole::Scientist);
}

void USkillTreeWidget::OnEngineeringClicked()
{
	SelectRole(EPressureSuitRole::Engineering);
}

void USkillTreeWidget::OnMedicalClicked()
{
	SelectRole(EPressureSuitRole::Medical);
}

void USkillTreeWidget::OnSkillUnlocked(const FString& SkillID)
{
	if (!RunOutcomeSubsystem || !SkillTreeSubsystem)
		return;

	// Points first, falling back to banked currency. The subsystem re-checks legality and derives
	// the price itself, so the widget cannot buy past a prerequisite or name its own cost.
	if (!RunOutcomeSubsystem->UnlockClassSkill(CurrentSelectedRole, SkillID))
	{
		RunOutcomeSubsystem->UnlockClassSkillWithCurrency(CurrentSelectedRole, SkillID);
	}

	RefreshAllSkillEntries();
}

void USkillTreeWidget::RefreshAllSkillEntries()
{
	UpdatePointsDisplay();
	PopulateSkillsForRole();
}
