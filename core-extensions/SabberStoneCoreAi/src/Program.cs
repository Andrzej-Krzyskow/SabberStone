using System;
using SabberStoneCore.Config;
using SabberStoneCore.Enums;
using SabberStoneCoreAi.POGame;
using SabberStoneCoreAi.Agent.ExampleAgents;
using SabberStoneCoreAi.Agent;
using SabberStoneCoreAi.src.Agent;
using SabberStoneCoreAi.Meta;
using SabberStoneCore.Model;
using System.Collections.Generic;


namespace SabberStoneCoreAi
{
	internal class Program
	{
		private static CardClass stringToCardClass(string c ) {
			if (c.Equals("MAGE"))
				return CardClass.MAGE;
			if (c.Equals("PALADIN"))
				return CardClass.PALADIN;
			if (c.Equals("PRIEST"))
				return CardClass.PRIEST;

			if (c.Equals("DRUID"))
				return CardClass.DRUID;
			if (c.Equals("HUNTER"))
				return CardClass.HUNTER;
			if (c.Equals("ROGUE"))
				return CardClass.ROGUE;

			if (c.Equals("SHAMAN"))
				return CardClass.SHAMAN;
			if (c.Equals("WARLOCK"))
				return CardClass.WARLOCK;
			if (c.Equals("WARRIOR"))
				return CardClass.WARRIOR;


			throw new Exception("CARD CLASS NOT VALID");

		}

		private static List<Card> stringToDeck(string c)
		{
			if (c.Equals("RenoKazakusMage"))
				return Decks.RenoKazakusMage;
			if (c.Equals("MidrangeJadeShaman")) 
				return Decks.MidrangeJadeShaman;
			if (c.Equals("AggroPirateWarrior"))
				return Decks.AggroPirateWarrior;
			throw new Exception("DECK DOES NOT EXIST");

		}

		private static GameConfig gameConfigCoevoluationary(string[] args) {
			GameConfig gameConfig = new GameConfig
			{
				StartPlayer = 1,
				Player1HeroClass = stringToCardClass(args[1]),
				Player2HeroClass = stringToCardClass(args[4]),
				FillDecks = false,
				Logging = false,
				Player1Deck = stringToDeck(args[0]),
				Player2Deck = stringToDeck(args[3]) //RenoKazakusMage
			};

			return gameConfig;

		}


		

		private static void Main(string[] args)
		{

			
			Console.WriteLine("Setup gameConfig");



			//todo: rename to Main
			/*GameConfig gameConfig = new GameConfig
			{
				StartPlayer = 1,
				Player1HeroClass = CardClass.MAGE,
				Player2HeroClass = CardClass.SHAMAN,
				FillDecks = false,
				Logging = false,
				Player1Deck = Decks.RenoKazakusMage,
				Player2Deck = Decks.MidrangeJadeShaman //RenoKazakusMage
			};


			/*foreach (Card c in Cards.All)
			{
				Console.WriteLine(c.Name);
			}*/

			GameConfig gameConfig = gameConfigCoevoluationary(args);

			Console.WriteLine("Setup POGameHandler");
			// MidrangeJadeShaman SHAMAN
			// AggroPirateWarrior WARRIOR
			// RenoKazakusMage MAGE
			// ParametricGreedyAgent
			// ModifiedParametricGreedyAgent63
			// ModifiedParametricGreedyAgent63Smooth
			// ModifiedParametricGreedyAgent28
			// ModifiedParametricGreedyAgent21Depth
			// ModifiedParametricGreedyAgent28Normalaized

			AbstractAgent player1agent = new ModifiedParametricGreedyAgent28Normalaized();
			((ModifiedParametricGreedyAgent28Normalaized)player1agent).setAgeintWeightsFromString(args[2]);
			AbstractAgent player2agent = new ModifiedParametricGreedyAgent28Normalaized();
			((ModifiedParametricGreedyAgent28Normalaized)player2agent).setAgeintWeightsFromString(args[5]);
			POGameHandler gameHandler = new POGameHandler(gameConfig, player1agent, player2agent, debug:false);
			gameConfig.StartPlayer = -1; //Pick random start player

			Console.WriteLine("STARTING GAMES");
			int numGames = Int32.Parse(args[6]);

			gameHandler.PlayGames(numGames);
			GameStats gameStats = gameHandler.getGameStats();
			//gameStats.printResults();
			int p1wins = gameStats.PlayerA_Wins;
			int p2wins = gameStats.PlayerB_Wins;

			Console.WriteLine(p1wins + " " + p2wins + " " + numGames + " " +
				gameStats.PlayerA_TurnsToWin + " " +
				gameStats.PlayerA_TurnsToLose + " " +
				gameStats.PlayerA_HealthDifferenceWinning + " " +
				gameStats.PlayerA_HealthDifferenceLosing
			);

			/*			Console.WriteLine("p1wins " + p1wins + " p2wins " + p2wins+ " numGames " + numGames+ "\nPlayerA_TurnsToWin " +
							gameStats.PlayerA_TurnsToWin+ "\nPlayerA_TurnsToLose " +
							gameStats.PlayerA_TurnsToLose+ "\nPlayerA_HealthDifferenceWinning " +
							gameStats.PlayerA_HealthDifferenceWinning + "\nPlayerA_HealthDifferenceLosing " +
							gameStats.PlayerA_HealthDifferenceLosing
							);*/



			//Console.ReadLine();

			// 21 my base
			/*
			 0.464811721#0.957010141#0.040338326#0.67701262#0.332088314#0.599264904#0#0#1#1#1#0.091104966#0.684484708#0.369738304#0.323052802#1#0.193644695#1#0.249525823#0.350936521#1
			*/

			// 21 depth
			/*
			 0.529172589472622#0.922844373638845#0#0#1#0.97740797893963#0.522667074764935#0.13107237590803#1#0.573481513675203#0.820908326273313#1#0.762014192221083#0#0.846901278455558#0.233434187541821#0.451355839928914#0#0#1#1
			*/

			// 63
			/*
			  0#0.838073451#0.369418052#0.77217592#0.612345931#0#1#0.279296808#1#0.039908815#0.937169411#1#0.622260112#0#0.55344352#0.78854921#0.343600993#0#0.343786801#1#1#0.191982477#0.552115935#0.315879891#1#0.732131369#0.872780909#0.628300921#0.614445716#1#0.752127346#0.800859059#0.805731203#0.244951239#0.703863389#0.458258308#0.452925122#0.066812968#0.805020043#0.644011807#0.493530341#0.676429882#0.491008555#1#0#0.584559439#0.929349863#0.541189268#1#0#0#0.97891184#0.708361817#1#0.182623231#0.019490829#1#0.443664583#0.630470581#1#0#1#0.486371358
			 */

			// 63 smooth
			/*
			  0.50183096343015#0.742345136374095#0#1#0.788967189846087#1#0.58019040024809#0#0.264508409631812#0.491884957258678#0.417088307533637#0.0998344107800981#0.312599962170786#1#0#0.279760334253207#0.469499077972434#0.511143276049166#0.306638552324898#0.704016565497176#0.347196077430126#0.372269208241967#1#0.573529477162427#0.478299687284229#0.0943804780364997#1#0#0.568385191539713#0#0.352433458663134#0#0#0.68074720817694#0#0.695241076410066#0.211022173926576#1#0.679374692176487#0.589091367411266#0#0#0.983072968018574#1#0.873833036562193#0.577481377245474#0.194016551354299#1#0.636185001683579#0#0.39191684186863#1#0.149059762034475#0#0.26151978270587#0.532534497260067#0#0.738243327066828#0.173110645291023#0.176199558424364#1#0#0.857491054669108
			 */

			// 28
			/*
			 0.9622560353455828#1#0#0#1#1#1#0#0.86147339157364#1#0.5430266096979701#1#0#0.17621606443353027#1#0.4104209220994927#0.9374832102214393#1#0.29276559472066643#0.01825896895584212#0.28901297450699664#0.6247405241351475#0#0.2299751081125314#0.7157675822536926#0.44551237594442145#0.7088354719260018#1
			 */

			// 28_normalized
			/*
			0.4489769376909381#1#0#0.2200813583097922#0.36904127870754105#0.5734997567308384#0.7609641739977115#0#1#1#0.8855302018224294#0.8306653004086676#0.5377170358339709#0.6550543815442608#0.2772477549959537#0.9592308396183514#0#0.24293859078887203#0.2529414637771258#0.9405997864481604#0#0.8282849886177859#0.7886381793044395#0.24788606446216535#0.4452603904961968#0.8513638103721802#0.09766786771815637#0.4317827066736215
			*/

			// researchers
			/*
			  0.338317197#0.934667132#0.093176193#0#0.751099025#1#0.961847886#0#1#0.552937948#0.596713458#0#1#0#0#1#0#0.002140127#0.371668433#0.169469073#0
			 */
		}
	}
}
