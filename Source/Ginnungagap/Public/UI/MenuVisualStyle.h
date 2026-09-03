#pragma once

#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/TextBlock.h"

namespace GinnungagapMenuStyle
{
	inline const FLinearColor Graphite(0.020f, 0.027f, 0.030f, 0.98f);
	inline const FLinearColor DisplayTeal(0.055f, 0.145f, 0.150f, 1.0f);
	inline const FLinearColor DisplayTealHover(0.080f, 0.245f, 0.250f, 1.0f);
	inline const FLinearColor SafetyAmber(0.74f, 0.29f, 0.075f, 1.0f);
	inline const FLinearColor CryoWhite(0.70f, 0.80f, 0.79f, 1.0f);
	inline const FLinearColor MutedSteel(0.34f, 0.40f, 0.39f, 1.0f);
	inline const FLinearColor FaultRed(0.54f, 0.12f, 0.055f, 1.0f);

	inline FSlateBrush MakeTerminalBrush(bool bActive=false)
	{
		FSlateBrush Brush;
		Brush.DrawAs=ESlateBrushDrawType::RoundedBox;
		Brush.TintColor=FSlateColor(bActive?FLinearColor(0.025f,0.070f,0.072f,0.985f):Graphite);
		Brush.OutlineSettings.CornerRadii=FVector4(3.0f,3.0f,3.0f,3.0f);
		Brush.OutlineSettings.Width=bActive?2.0f:1.0f;
		Brush.OutlineSettings.Color=FSlateColor(bActive?FLinearColor(0.20f,0.48f,0.49f,0.88f):FLinearColor(0.20f,0.26f,0.26f,0.82f));
		return Brush;
	}

	inline void ApplyTerminalPanel(UBorder* Border,bool bActive=false)
	{
		if(Border)Border->SetBrush(MakeTerminalBrush(bActive));
	}

	inline void ApplyTerminalText(UTextBlock* Text,int32 Size,const FLinearColor& Color,bool bTracked=false)
	{
		if(!Text)return;
		FSlateFontInfo Font(Text->GetFont().FontObject,Size);
		Font.LetterSpacing=bTracked?120:20;
		Text->SetFont(Font);
		Text->SetColorAndOpacity(FSlateColor(Color));
	}

	inline void ApplyButton(UButton* Button,bool bPrimary=false)
	{
		if(!Button)return;
		FButtonStyle Style=Button->GetStyle();
		FSlateBrush Normal=Style.Normal;Normal.DrawAs=ESlateBrushDrawType::RoundedBox;Normal.TintColor=FSlateColor(bPrimary?DisplayTeal:FLinearColor(0.035f,0.050f,0.052f,1.0f));
		Normal.OutlineSettings.CornerRadii=FVector4(2.0f,2.0f,2.0f,2.0f);
		Normal.OutlineSettings.Width=1.0f;
		Normal.OutlineSettings.Color=FSlateColor(bPrimary?FLinearColor(0.18f,0.48f,0.50f,0.75f):FLinearColor(0.24f,0.30f,0.30f,0.65f));
		FSlateBrush Hovered=Normal;Hovered.TintColor=FSlateColor(bPrimary?DisplayTealHover:FLinearColor(0.075f,0.135f,0.140f,1.0f));Hovered.OutlineSettings.Color=FSlateColor(SafetyAmber);
		FSlateBrush Pressed=Normal;Pressed.TintColor=FSlateColor(SafetyAmber);Pressed.OutlineSettings.Color=FSlateColor(CryoWhite);
		FSlateBrush Disabled=Normal;Disabled.TintColor=FSlateColor(FLinearColor(0.025f,0.04f,0.05f,0.55f));
		Style.SetNormal(Normal);Style.SetHovered(Hovered);Style.SetPressed(Pressed);Style.SetDisabled(Disabled);
		Style.SetNormalPadding(FMargin(18.0f,12.0f));Style.SetPressedPadding(FMargin(18.0f,14.0f,18.0f,10.0f));
		Button->SetStyle(Style);
	}
}
