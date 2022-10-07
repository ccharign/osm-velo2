-- phpMyAdmin SQL Dump
-- version 4.9.7
-- https://www.phpmyadmin.net/
--
-- Hôte : localhost:3306
-- Généré le : Dim 13 fév. 2022 à 12:38
-- Version du serveur :  10.3.32-MariaDB
-- Version de PHP : 7.3.33

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de données : `oafo2293_itineraires`
--

-- --------------------------------------------------------


--
-- Déchargement des données de la table `dijk_chemin_d`
--

INSERT INTO `dijk_chemin_d` (`id`, `ar`, `p_détour`, `étapes_texte`, `interdites_texte`, `utilisateur`, `dernier_p_modif`, `début`, `fin`, `interdites_début`, `interdites_fin`, `zone_id`) VALUES
(1, 1, 0.3, 'rue des Véroniques, ;rue Voltaire, ;rue Sambre et Meuse, ;cours Bosquet, ;place de la République, ', '', NULL, 0.00865048084164232, 'rue des Véroniques, ;rue Voltaire, ;rue Sambre et Meuse, ;cours Bosquet, ;place de la République, ', 'rue des Véroniques, ;rue Voltaire, ;rue Sambre et Meuse, ;cours Bosquet, ;place de la République, ', '', '', 1),
(2, 1, 0.3, 'rue des réparatrices, ;avenue San Carlos, ;avenue des acacias, ;avenue de Montebello, ;avenue Bié-Moulié, ;rue Gutenberg, ', '', NULL, 0, 'rue des réparatrices, ;avenue San Carlos, ;avenue des acacias, ;avenue de Montebello, ;avenue Bié-Moulié, ;rue Gutenberg, ', 'rue des réparatrices, ;avenue San Carlos, ;avenue des acacias, ;avenue de Montebello, ;avenue Bié-Moulié, ;rue Gutenberg, ', '', '', 1),
(3, 1, 0.3, 'avenue du Loup, ;chemin des écoliers, ;rue Mozart, ;chemin Guilhem, ', '', NULL, 0, 'avenue du Loup, ;chemin des écoliers, ;rue Mozart, ;chemin Guilhem, ', 'avenue du Loup, ;chemin des écoliers, ;rue Mozart, ;chemin Guilhem, ', '', '', 1),
(4, 1, 0.3, 'Rond-Point Éric Tabarly, ;Chemin Labriart, ;Rue Cassiopée, ;Rue Blanqui, ;Rue Paul Bert, ;Rue Marx Dormoy, ;CSTJF, ', '', NULL, 0.0006576895696455292, 'Rond-Point Éric Tabarly, ;Chemin Labriart, ;Rue Cassiopée, ;Rue Blanqui, ;Rue Paul Bert, ;Rue Marx Dormoy, ;CSTJF, ', 'Rond-Point Éric Tabarly, ;Chemin Labriart, ;Rue Cassiopée, ;Rue Blanqui, ;Rue Paul Bert, ;Rue Marx Dormoy, ;CSTJF, ', '', '', 1),
(5, 0, 0.2, 'rue d\'étigny, ;place gramont, ;rue tran, ;place de la libération, ;rue gassiot, ;rue carnot, ;rue cazaubon norbert, ;boulevard d\'alsace-lorraine, ;cours lyautey, ;avenue de saragosse, ;avenue de buros, ;84 avenue de buros, ', '', NULL, 0.0012525936140620369, 'rue d\'étigny, ;place gramont, ;rue tran, ;place de la libération, ;rue gassiot, ;rue carnot, ;rue cazaubon norbert, ;boulevard d\'alsace-lorraine, ;cours lyautey, ;avenue de saragosse, ;avenue de buros, ;84 avenue de buros, ', 'rue d\'étigny, ;place gramont, ;rue tran, ;place de la libération, ;rue gassiot, ;rue carnot, ;rue cazaubon norbert, ;boulevard d\'alsace-lorraine, ;cours lyautey, ;avenue de saragosse, ;avenue de buros, ;84 avenue de buros, ', '', '', 1),
(6, 1, 0.2, 'véloroute V81, 64320 mazères-lezons;véloroute V81, 64320 bizanos;13 rue de verdun, 64320 bizanos;avenue albert 1er, 64320 bizanos;69 rue pasteur, 64320 bizanos;58 rue pasteur, 64320 bizanos;35 rue pasteur, 64320 bizanos;11 rue pasteur, 64320 bizanos;13 avenue de barèges, 64000 PAU;avenue léon say, 64000 PAU;rue léon daran, ;place saint-louis de gonzague, ;rue valéry meunier, ;24 rue du maréchal foch, ;rue serviez, ;rue carnot, ;rue cazaubon norbert, ;cours lyautey, ;62 avenue louis sallenave, ;88 avenue louis sallenave, ;145 avenue philippon, ;347 Boulevard du Cami Salié, ', '', NULL, 0.029500266351396288, 'véloroute V81, 64320 mazères-lezons;véloroute V81, 64320 bizanos;13 rue de verdun, 64320 bizanos;avenue albert 1er, 64320 bizanos;69 rue pasteur, 64320 bizanos;58 rue pasteur, 64320 bizanos;35 rue pasteur, 64320 bizanos;11 rue pasteur, 64320 bizanos;13 av', ' ;place saint-louis de gonzague, ;rue valéry meunier, ;24 rue du maréchal foch, ;rue serviez, ;rue carnot, ;rue cazaubon norbert, ;cours lyautey, ;62 avenue louis sallenave, ;88 avenue louis sallenave, ;145 avenue philippon, ;347 Boulevard du Cami Salié, ', '', '', 1),
(7, 1, 0.2, 'rue de Lagardère, ;avenue Trespoey, ;place Clémenceau, ;rue Serviez, ;place des sept cantons, ;rue Bernadotte, ;rue de Liège, ;rue Lapouble, ', '', NULL, 0.020036641147308153, 'rue de Lagardère, ;avenue Trespoey, ;place Clémenceau, ;rue Serviez, ;place des sept cantons, ;rue Bernadotte, ;rue de Liège, ;rue Lapouble, ', 'rue de Lagardère, ;avenue Trespoey, ;place Clémenceau, ;rue Serviez, ;place des sept cantons, ;rue Bernadotte, ;rue de Liège, ;rue Lapouble, ', '', '', 1),
(8, 1, 0.4, '4 rue Mourot, ;rue Montpensier, ;rond-point du souvenir français, ;avenue de montardon, ;boulevard du cami salié, ;allée buffon, ;chemin de la forêt bastard, ', '', NULL, 0.007994808177451162, '4 rue Mourot, ;rue Montpensier, ;rond-point du souvenir français, ;avenue de montardon, ;boulevard du cami salié, ;allée buffon, ;chemin de la forêt bastard, ', '4 rue Mourot, ;rue Montpensier, ;rond-point du souvenir français, ;avenue de montardon, ;boulevard du cami salié, ;allée buffon, ;chemin de la forêt bastard, ', '', '', 1),
(9, 1, 0.4, '4 rue Ramond de Carbonnières, ;avenue Henry Russel, ;avenue Trespoey, ;Lycée Barthou, ', '', NULL, 0, '4 rue Ramond de Carbonnières, ;avenue Henry Russel, ;avenue Trespoey, ;Lycée Barthou, ', '4 rue Ramond de Carbonnières, ;avenue Henry Russel, ;avenue Trespoey, ;Lycée Barthou, ', '', '', 1),
(10, 0, 0.3, 'rue d\'Artouste, ;avenue d\'Attigny, ;avenue de Montardon, ;rue du Pin, ;boulevard Recteur Jean Sarrailh, ;rue Victor Ladevèze, ;rue du père Pardies, ;rue Viard, ;rue Montpensier, ;rue Serviez, ;place Georges Clémenceau, ', '', NULL, 0.004385560561082604, 'rue d\'Artouste, ;avenue d\'Attigny, ;avenue de Montardon, ;rue du Pin, ;boulevard Recteur Jean Sarrailh, ;rue Victor Ladevèze, ;rue du père Pardies, ;rue Viard, ;rue Montpensier, ;rue Serviez, ;place Georges Clémenceau, ', 'rue d\'Artouste, ;avenue d\'Attigny, ;avenue de Montardon, ;rue du Pin, ;boulevard Recteur Jean Sarrailh, ;rue Victor Ladevèze, ;rue du père Pardies, ;rue Viard, ;rue Montpensier, ;rue Serviez, ;place Georges Clémenceau, ', '', '', 1),
(11, 0, 0.3, 'place Georges Clémenceau, ;rue Serviez, ;rue Gassiot, ;rue Mourot, ;place Albert 1er, ;rue Duplaa, ;rue Perpignaa, ;rue de Monpezat, ;rue Montpensier, ;parc Lawrence, ;rue du père Pardies, ;rue Victor Ladevèze, ;boulevard Recteur Jean Sarrailh, ;rue du Pin, ;71 avenue de Montardon, ;avenue d\'Attigny, ;rue d\'Artouste, ', '', NULL, 0.018919623400954582, 'place Georges Clémenceau, ;rue Serviez, ;rue Gassiot, ;rue Mourot, ;place Albert 1er, ;rue Duplaa, ;rue Perpignaa, ;rue de Monpezat, ;rue Montpensier, ;parc Lawrence, ;rue du père Pardies, ;rue Victor Ladevèze, ;boulevard Recteur Jean Sarrailh, ;rue du Pi', 't, ;place Albert 1er, ;rue Duplaa, ;rue Perpignaa, ;rue de Monpezat, ;rue Montpensier, ;parc Lawrence, ;rue du père Pardies, ;rue Victor Ladevèze, ;boulevard Recteur Jean Sarrailh, ;rue du Pin, ;71 avenue de Montardon, ;avenue d\'Attigny, ;rue d\'Artouste, ', '', '', 1),
(12, 0, 0.2, 'rue Montpensier, ;rue Serviez, ;rue Latapie, ;rue Gambetta, ;allée Alfred de Musset, ', '', NULL, 0.007378181156274588, 'rue Montpensier, ;rue Serviez, ;rue Latapie, ;rue Gambetta, ;allée Alfred de Musset, ', 'rue Montpensier, ;rue Serviez, ;rue Latapie, ;rue Gambetta, ;allée Alfred de Musset, ', '', '', 1),
(13, 1, 0.3, 'Rue dou barthouil, 64320 ousse;allée de l’église, 64320 lee;Avenue beau soleil, ;Avenue trespoey, ;Avenue edouard VII, ;allée alfred de Musset, ;rue Louis Barthou, ', '', NULL, 0, 'Rue dou barthouil, 64320 ousse;allée de l’église, 64320 lee;Avenue beau soleil, ;Avenue trespoey, ;Avenue edouard VII, ;allée alfred de Musset, ;rue Louis Barthou, ', 'Rue dou barthouil, 64320 ousse;allée de l’église, 64320 lee;Avenue beau soleil, ;Avenue trespoey, ;Avenue edouard VII, ;allée alfred de Musset, ;rue Louis Barthou, ', '', '', 1),
(14, 1, 0.3, 'rue des écoles, 64140 Lons;Chemin des vignes, 64140 Lons;Rue du Mohedan, Billère;rue des Muses, Billère;Avenue de la République, 64140 Billère;Rue Jeanne Lassansaa, 64140 Billère;Rue Claverie, 64140 Billère;Rue des Marnières, 64140 Billère;Rue des Marnières, 64000 Pau;Boulevard Edouard Herriot, ;50 Boulevard Alsace Lorraine, ;Avenue Edouard VII, ', '', NULL, 0, 'rue des écoles, 64140 Lons;Chemin des vignes, 64140 Lons;Rue du Mohedan, Billère;rue des Muses, Billère;Avenue de la République, 64140 Billère;Rue Jeanne Lassansaa, 64140 Billère;Rue Claverie, 64140 Billère;Rue des Marnières, 64140 Billère;Rue des Marnièr', 's, Billère;Avenue de la République, 64140 Billère;Rue Jeanne Lassansaa, 64140 Billère;Rue Claverie, 64140 Billère;Rue des Marnières, 64140 Billère;Rue des Marnières, 64000 Pau;Boulevard Edouard Herriot, ;50 Boulevard Alsace Lorraine, ;Avenue Edouard VII, ', '', '', 1),
(15, 0, 0.3, 'rue des veroniques, ;rue regina, ;parc beaumont, ', '', NULL, 0.0038722917714962544, 'rue des veroniques, ;rue regina, ;parc beaumont, ', 'rue des veroniques, ;rue regina, ;parc beaumont, ', '', '', 1),
(16, 1, 0.3, 'rue des veroniques, ;avenue de l’yser, bizanos;avenue de la paix, gelos;route des coteaux de guindalos, jurançon', '', NULL, 0, 'rue des veroniques, ;avenue de l’yser, bizanos;avenue de la paix, gelos;route des coteaux de guindalos, jurançon', 'rue des veroniques, ;avenue de l’yser, bizanos;avenue de la paix, gelos;route des coteaux de guindalos, jurançon', '', '', 1),
(17, 1, 0.3, 'rue ramond de carbonnieres, ;rue du marechal joffre, ;rue des cordeliers, ;rue marca, ', '', NULL, 0.008306835564335363, 'rue ramond de carbonnieres, ;rue du marechal joffre, ;rue des cordeliers, ;rue marca, ', 'rue ramond de carbonnieres, ;rue du marechal joffre, ;rue des cordeliers, ;rue marca, ', '', '', 1),
(18, 1, 0.2, 'rue serviez, 64000 pau;rue jean jacques de monaix, 64000 pau;avenue de buros, 64000 pau', '', NULL, 0, 'rue serviez, 64000 pau;rue jean jacques de monaix, 64000 pau;avenue de buros, 64000 pau', 'rue serviez, 64000 pau;rue jean jacques de monaix, 64000 pau;avenue de buros, 64000 pau', '', '', 1),
(19, 1, 0.2, 'rue des veroniques, 64000 Pau;chemin des ecoliers, 64000 Pau;allee françois truffaut, 64000 Pau;avenue de la malsence, 64000 Pau;avenue de lons, 64140 Billère;Rue du Lacaou, 64140 Billère;Europub, 64140 Billère', '', NULL, 0.038109361535211404, 'rue des veroniques, 64000 Pau;chemin des ecoliers, 64000 Pau;allee françois truffaut, 64000 Pau;avenue de la malsence, 64000 Pau;avenue de lons, 64140 Billère;Rue du Lacaou, 64140 Billère;Europub, 64140 Billère', 'rue des veroniques, 64000 Pau;chemin des ecoliers, 64000 Pau;allee françois truffaut, 64000 Pau;avenue de la malsence, 64000 Pau;avenue de lons, 64140 Billère;Rue du Lacaou, 64140 Billère;Europub, 64140 Billère', '', '', 1),
(20, 0, 0.2, 'palais des sports, 64000 Pau;allee cordorcet, 64000 Pau;avenue duffau, 64000 Pau;place royale, 64000 Pau', '', NULL, 0, 'palais des sports, 64000 Pau;allee cordorcet, 64000 Pau;avenue duffau, 64000 Pau;place royale, 64000 Pau', 'palais des sports, 64000 Pau;allee cordorcet, 64000 Pau;avenue duffau, 64000 Pau;place royale, 64000 Pau', '', '', 1),
(21, 1, 0.2, 'rue des veroniques, 64000 Pau;rue laffite, 64140 Billère;chemin lapassade, 64140 Lons;rue flandre dunkerque, 64230 Lescar;rue benjamin franklin, 64230 Lescar', '', NULL, 0, 'rue des veroniques, 64000 Pau;rue laffite, 64140 Billère;chemin lapassade, 64140 Lons;rue flandre dunkerque, 64230 Lescar;rue benjamin franklin, 64230 Lescar', 'rue des veroniques, 64000 Pau;rue laffite, 64140 Billère;chemin lapassade, 64140 Lons;rue flandre dunkerque, 64230 Lescar;rue benjamin franklin, 64230 Lescar', '', '', 1),
(22, 0, 0.2, 'rue des veroniques, 64000 Pau;place royale, 64000 Pau', 'boulevard barbanègre, ;rue Latapie, ', NULL, 0, 'rue des veroniques, 64000 Pau;place royale, 64000 Pau', 'rue des veroniques, 64000 Pau;place royale, 64000 Pau', 'boulevard barbanègre, ;rue Latapie, ', 'boulevard barbanègre, ;rue Latapie, ', 1),
(23, 0, 0.2, 'rue des veroniques, 64000 Pau;place royale, 64000 Pau', 'boulevard barbanègre, ', NULL, 0, 'rue des veroniques, 64000 Pau;place royale, 64000 Pau', 'rue des veroniques, 64000 Pau;place royale, 64000 Pau', 'boulevard barbanègre, ', 'boulevard barbanègre, ', 1),
(24, 0, 0.2, 'place royale, 64000 Pau;rue louis barthou, 64000 Pau;allee alfred de musset, 64000 Pau;avenue trespoey, 64000 Pau;avenue de montebello, 64000 Pau;rue des veroniques, 64000 Pau', 'boulevard barbanègre, ;avenue du général Leclerc, ', NULL, 0.02619618270107097, 'place royale, 64000 Pau;rue louis barthou, 64000 Pau;allee alfred de musset, 64000 Pau;avenue trespoey, 64000 Pau;avenue de montebello, 64000 Pau;rue des veroniques, 64000 Pau', 'place royale, 64000 Pau;rue louis barthou, 64000 Pau;allee alfred de musset, 64000 Pau;avenue trespoey, 64000 Pau;avenue de montebello, 64000 Pau;rue des veroniques, 64000 Pau', 'boulevard barbanègre, ;avenue du général Leclerc, ', 'boulevard barbanègre, ;avenue du général Leclerc, ', 1),
(25, 0, 0.15, 'rue des cordeliers, 64000 Pau;rue saint jacques, 64000 Pau;halle des sports uppa, 64000 Pau', '', NULL, 0, 'rue des cordeliers, 64000 Pau;rue saint jacques, 64000 Pau;halle des sports uppa, 64000 Pau', 'rue des cordeliers, 64000 Pau;rue saint jacques, 64000 Pau;halle des sports uppa, 64000 Pau', '', '', 1),
(26, 0, 0.15, '16 rue des veroniques, 64000 Pau;38 rue du gui, 64000 Pau', 'bd de la paix, ', NULL, 0, '16 rue des veroniques, 64000 Pau;38 rue du gui, 64000 Pau', '16 rue des veroniques, 64000 Pau;38 rue du gui, 64000 Pau', 'bd de la paix, ', 'bd de la paix, ', 1),
(27, 0, 0.15, '38 rue du gui, 64000 Pau;avenue de montardon, 64000 Pau;rue albert camus, 64000 Pau;rue pasteur, 64000 Pau;rue guichenne, 64000 Pau;rue samonzet, 64000 Pau;rue matthieux lalanne, 64000 Pau;college marguerite de navarre, 64000 Pau', '', NULL, 0.017275536029881407, '38 rue du gui, 64000 Pau;avenue de montardon, 64000 Pau;rue albert camus, 64000 Pau;rue pasteur, 64000 Pau;rue guichenne, 64000 Pau;rue samonzet, 64000 Pau;rue matthieux lalanne, 64000 Pau;college marguerite de navarre, 64000 Pau', '38 rue du gui, 64000 Pau;avenue de montardon, 64000 Pau;rue albert camus, 64000 Pau;rue pasteur, 64000 Pau;rue guichenne, 64000 Pau;rue samonzet, 64000 Pau;rue matthieux lalanne, 64000 Pau;college marguerite de navarre, 64000 Pau', '', '', 1),
(28, 0, 0.05, '16 rue des veroniques, 64000 Pau;piste cyclable leon blum, 64000 Pau;rue gutemberg, 64000 Pau', '', NULL, 0, '16 rue des veroniques, 64000 Pau;piste cyclable leon blum, 64000 Pau;rue gutemberg, 64000 Pau', '16 rue des veroniques, 64000 Pau;piste cyclable leon blum, 64000 Pau;rue gutemberg, 64000 Pau', '', '', 1),
(29, 1, 0.25, '14 boulevard de la paix, 64000 Pau;impasse clos saint andre, 64000 Pau;rue paul langevin, 64000 Pau;avenue stravinsky, 64000 Pau;avenue jean mermoz, 64000 Pau', '', NULL, 0, '14 boulevard de la paix, 64000 Pau;impasse clos saint andre, 64000 Pau;rue paul langevin, 64000 Pau;avenue stravinsky, 64000 Pau;avenue jean mermoz, 64000 Pau', '14 boulevard de la paix, 64000 Pau;impasse clos saint andre, 64000 Pau;rue paul langevin, 64000 Pau;avenue stravinsky, 64000 Pau;avenue jean mermoz, 64000 Pau', '', '', 1),
(30, 0, 0.15, 'rue des véroniques, 64000 Pau;Piste cyclable du Balaïtous, 64000 Pau;Chemin Lapassade, 64000 Pau;rue benjamin Franklin, 64230 Lescar', '', NULL, 0, 'rue des véroniques, 64000 Pau;Piste cyclable du Balaïtous, 64000 Pau;Chemin Lapassade, 64000 Pau;rue benjamin Franklin, 64230 Lescar', 'rue des véroniques, 64000 Pau;Piste cyclable du Balaïtous, 64000 Pau;Chemin Lapassade, 64000 Pau;rue benjamin Franklin, 64230 Lescar', '', '', 1),
(31, 0, 0.15, 'rue des véroniques, 64000 Pau;rue benjamin Franklin, 64230 Lescar', 'allée de l’arrémoulit, Lons', NULL, 0, 'rue des véroniques, 64000 Pau;rue benjamin Franklin, 64230 Lescar', 'rue des véroniques, 64000 Pau;rue benjamin Franklin, 64230 Lescar', 'allée de l’arrémoulit, Lons', 'allée de l’arrémoulit, Lons', 1),
(32, 1, 0.1, 'rue des véroniques, 64000 Pau, France;avenue du béarn, 64320 Lee, France;2 route de pau, 64320 Ousse, France', '', NULL, NULL, 'rue des véroniques, 64000 Pau, France;avenue du béarn, 64320 Lee, France;2 route de pau, 64320 Ousse, France', 'rue des véroniques, 64000 Pau, France;avenue du béarn, 64320 Lee, France;2 route de pau, 64320 Ousse, France', '', '', 1),
(33, 1, 0.1, 'Lycée Louis Barthou, 64000 Pau, France;Rue du chanoine laborde, 64000 Pau, France;Lidl, 64000 Pau, France', '', NULL, NULL, 'Lycée Louis Barthou, 64000 Pau, France;Rue du chanoine laborde, 64000 Pau, France;Lidl, 64000 Pau, France', 'Lycée Louis Barthou, 64000 Pau, France;Rue du chanoine laborde, 64000 Pau, France;Lidl, 64000 Pau, France', '', '', 1),
(34, 1, 0.1, '13 rue castetnau, 64000 Pau, France;rue du chanoine laborde, 64000 Pau, France;Halle des sports UPPA, 64000 Pau, France', '', NULL, NULL, '13 rue castetnau, 64000 Pau, France;rue du chanoine laborde, 64000 Pau, France;Halle des sports UPPA, 64000 Pau, France', '13 rue castetnau, 64000 Pau, France;rue du chanoine laborde, 64000 Pau, France;Halle des sports UPPA, 64000 Pau, France', '', '', 2),
(35, 1, 0.1, '16 rue des véroniques, 64000 Pau, France;rue ronsard, 64000 Pau, France;Halle des sports UPPA, 64000 Pau, France', '', NULL, NULL, '16 rue des véroniques, 64000 Pau, France;rue ronsard, 64000 Pau, France;Halle des sports UPPA, 64000 Pau, France', '16 rue des véroniques, 64000 Pau, France;rue ronsard, 64000 Pau, France;Halle des sports UPPA, 64000 Pau, France', '', '', 2),
(36, 0, 0.3, '16 rue des véroniques, 64000 Pau, France;rue jean monnet, 64000 Pau, France;Passage des Halles, 64000 Pau, France', 'rue samonzet', NULL, NULL, '16 rue des véroniques, 64000 Pau, France;rue jean monnet, 64000 Pau, France;Passage des Halles, 64000 Pau, France', '16 rue des véroniques, 64000 Pau, France;rue jean monnet, 64000 Pau, France;Passage des Halles, 64000 Pau, France', 'rue samonzet', 'rue samonzet', 2);

--
-- Index pour les tables déchargées
--

--
-- Index pour la table `dijk_chemin_d`
--
ALTER TABLE `dijk_chemin_d`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `Pas de chemins en double.` (`ar`,`p_détour`,`début`,`fin`,`interdites_début`,`interdites_fin`),
  ADD KEY `dijk_chemin_d_zone_id_8545faf5_fk_dijk_zone_id` (`zone_id`);

--
-- AUTO_INCREMENT pour les tables déchargées
--

--
-- AUTO_INCREMENT pour la table `dijk_chemin_d`
--
ALTER TABLE `dijk_chemin_d`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=37;

--
-- Contraintes pour les tables déchargées
--

--
-- Contraintes pour la table `dijk_chemin_d`
--
ALTER TABLE `dijk_chemin_d`
  ADD CONSTRAINT `dijk_chemin_d_zone_id_8545faf5_fk_dijk_zone_id` FOREIGN KEY (`zone_id`) REFERENCES `dijk_zone` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
