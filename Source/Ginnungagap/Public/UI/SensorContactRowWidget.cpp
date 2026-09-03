#include "SensorContactRowWidget.h"

#include "Components/Button.h"
#include "Components/TextBlock.h"
#include "Blueprint/WidgetTree.h"

void USensorContactRowWidget::NativeOnInitialized()
{
    Super::NativeOnInitialized();
    if (WidgetTree && !WidgetTree->RootWidget)
    {
        SelectButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), TEXT("ContactButton"));
        Label = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("ContactLabel"));
        SelectButton->AddChild(Label);
        WidgetTree->RootWidget = SelectButton;
        SelectButton->OnClicked.AddDynamic(this, &USensorContactRowWidget::HandleClicked);
    }
    RefreshLabel();
}

void USensorContactRowWidget::NativeConstruct()
{
    Super::NativeConstruct();
    // Focus needs the Slate tree, which exists only once the widget is constructed.
}

void USensorContactRowWidget::Configure(ASensorArraySystem* InSensorSource, const FSensorContact& InContact, bool bIsTracked)
{
    SensorSource = InSensorSource;
    Contact = InContact;
    bTracked = bIsTracked;
    RefreshLabel();
}

void USensorContactRowWidget::HandleClicked()
{
    if (SensorSource)
    {
        SensorSource->TrackContact(Contact);
        bTracked = true;
        RefreshLabel();
    }
}

void USensorContactRowWidget::RefreshLabel()
{
    if (!Label)
    {
        return;
    }
    const FString Identity = Contact.bIdentified ? Contact.DisplayName.ToString() : TEXT("UNKNOWN CONTACT");
    const TCHAR* PriorityMarker = Contact.bCriticalResource ? TEXT("[PRIORITY] ") : TEXT("");
    Label->SetText(FText::FromString(FString::Printf(TEXT("%s%s%-24s  %6.1f km  BRG %+06.1f"),
        bTracked ? TEXT("> ") : TEXT("  "), PriorityMarker, *Identity, Contact.DistanceKilometers, Contact.BearingDegrees)));
    Label->SetColorAndOpacity(FSlateColor(bTracked
        ? FLinearColor(0.3f, 1.0f, 0.55f)
        : (Contact.bCriticalResource ? FLinearColor(1.0f, 0.25f, 0.12f)
            : (Contact.bIdentified ? FLinearColor(0.72f, 0.9f, 0.92f) : FLinearColor(1.0f, 0.62f, 0.18f)))));
}
