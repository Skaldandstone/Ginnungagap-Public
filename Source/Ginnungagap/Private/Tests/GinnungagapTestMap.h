#pragma once

#include "CoreMinimal.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

namespace GinnungagapTestMap
{
	/**
	 * The demo map, or whatever -GinnungagapMap=<package path> names: the same look, station and
	 * route tests serve every ship. Shared here because the unity build folds the test files into
	 * one translation unit and a copy per file is a redefinition.
	 */
	inline FString Path()
	{
		FString Override;
		if (FParse::Value(FCommandLine::Get(), TEXT("GinnungagapMap="), Override) && !Override.IsEmpty())
		{
			return Override;
		}
		return TEXT("/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck");
	}
}
