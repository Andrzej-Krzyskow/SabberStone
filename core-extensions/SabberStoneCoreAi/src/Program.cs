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

			AbstractAgent player1agent = new ModifiedParametricGreedyAgent63Smooth();
			((ModifiedParametricGreedyAgent63Smooth)player1agent).setAgeintWeightsFromString(args[2]);
			AbstractAgent player2agent = new ModifiedParametricGreedyAgent63Smooth();
			((ModifiedParametricGreedyAgent63Smooth)player2agent).setAgeintWeightsFromString(args[5]);
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

			// my base 1
			/*
			  0.317548892#0.64751489#0#0#0.691774044#1#0#0#0.812790562#0.205625525#1#0.316685241#0.775303694#1#1#0#0#0#1#0.041051187#0.790651628
			 */

			// my base 2
			/*
			 0.464811721#0.957010141#0.040338326#0.67701262#0.332088314#0.599264904#0#0#1#1#1#0.091104966#0.684484708#0.369738304#0.323052802#1#0.193644695#1#0.249525823#0.350936521#1
			*/

			// modified-63 1
			/*
			  0.092872287#0#0.368088358#0.225431908#1#0.742770523#1#0.268155441#0#0.615064886#0.825956739#1#1#1#0.903470835#0#1#1#0.635465347#1#0.162638721#1#0.384545593#1#1#1#0.882923029#1#0.293708773#0.834379729#0#0#1#0#0.830118921#0.616145057#0.526511733#0#1#0#1#1#0.473691366#1#0#0.168229353#0.472131151#0.642929778#0.388772366#0.108080543#0.542110186#0.522338139#0#0.531550281#0.052149914#0#0.877995312#0.515583954#0.293272089#1#0.708716842#1#0.34528642
			 */

			// modified-63 2
			/*
			  0#0.838073451#0.369418052#0.77217592#0.612345931#0#1#0.279296808#1#0.039908815#0.937169411#1#0.622260112#0#0.55344352#0.78854921#0.343600993#0#0.343786801#1#1#0.191982477#0.552115935#0.315879891#1#0.732131369#0.872780909#0.628300921#0.614445716#1#0.752127346#0.800859059#0.805731203#0.244951239#0.703863389#0.458258308#0.452925122#0.066812968#0.805020043#0.644011807#0.493530341#0.676429882#0.491008555#1#0#0.584559439#0.929349863#0.541189268#1#0#0#0.97891184#0.708361817#1#0.182623231#0.019490829#1#0.443664583#0.630470581#1#0#1#0.486371358
			 */


			// modified-28 1
			/*
			 0.9622560353455828#1#0#0#1#1#1#0#0.86147339157364#1#0.5430266096979701#1#0#0.17621606443353027#1#0.4104209220994927#0.9374832102214393#1#0.29276559472066643#0.01825896895584212#0.28901297450699664#0.6247405241351475#0#0.2299751081125314#0.7157675822536926#0.44551237594442145#0.7088354719260018#1

			weights
			 #0.6247405241351475#0#0.2299751081125314#0.7157675822536926#0.44551237594442145#0.7088354719260018#1
			#0.5#0.5#0.5#0.5#0.5#0.5#0.5

			0.338317197#0.934667132#0.093176193#0#0.751099025#1#0.961847886#0#1#0.552937948#0.596713458#0#1#0#0#1#0#0.002140127#0.371668433#0.169469073#0#0.6247405241351475#0#0.2299751081125314#0.7157675822536926#0.44551237594442145#0.7088354719260018#1
			 */

			// researchers
			/*
			  0.338317197#0.934667132#0.093176193#0#0.751099025#1#0.961847886#0#1#0.552937948#0.596713458#0#1#0#0#1#0#0.002140127#0.371668433#0.169469073#0
			 */
		}
	}
}
