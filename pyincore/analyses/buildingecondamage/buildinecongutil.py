# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from pyincore import AnalysisUtil


class BuildingEconUtil:
    """Utility methods for the building damage analysis."""
    DEFAULT_FRAGILITY_KEY = "Non-Retrofit Fragility ID Code"
    DEFAULT_TSUNAMI_HMAX_FRAGILITY_KEY = "Non-Retrofit Inundation Fragility ID Code"
    DEFAULT_TSUNAMI_MMAX_FRAGILITY_KEY = "Non-Retrofit MomentumFlux Fragility ID Code"
    BLDG_STORIES = "no_stories"
    PROPERTIES = "properties"
    BLDG_PERIOD = "period"

    @staticmethod
    def get_hazard_demand_type(building, fragility_set, hazard_type):
        """Get hazard demand type.

        Args:
            building (obj): A JSON mapping of a geometric object from the inventory: current building.
            fragility_set (obj): A JSON description of fragility applicable to the building.
            hazard_type (str): A hazard type such as earthquake, tsunami etc.

        Returns:
            str: A hazard demand type.

        """
        fragility_hazard_type = fragility_set['demandType'].lower()
        hazard_demand_type = fragility_hazard_type

        if hazard_type.lower() == "earthquake":
            num_stories = building[BuildingEconUtil.PROPERTIES][BuildingEconUtil.BLDG_STORIES]
            # Get building period from the fragility if possible
            building_period = AnalysisUtil.get_building_period(num_stories, fragility_set)

            if fragility_hazard_type.endswith('sa') and fragility_hazard_type != 'sa':
                # This fixes a bug where demand type is in a format similar to 1.0 Sec Sa
                if len(fragility_hazard_type.split()) > 2:
                    building_period = fragility_hazard_type.split()[0]
                    fragility_hazard_type = "Sa"

            hazard_demand_type = fragility_hazard_type

            # This handles the case where some fragilities only specify Sa, others a specific period of Sa
            if not hazard_demand_type.endswith('pga'):
                # If the fragility does not contain the period calculation, check if the dataset has it
                if building_period == 0.0 and BuildingEconUtil.BLDG_PERIOD in building[BuildingEconUtil.PROPERTIES]:
                    if building[BuildingEconUtil.PROPERTIES][BuildingEconUtil.BLDG_PERIOD] > 0.0:
                        building_period = building[BuildingEconUtil.PROPERTIES][BuildingEconUtil.BLDG_PERIOD]

                hazard_demand_type = str(building_period) + " " + fragility_hazard_type
        elif hazard_type.lower() == "tsunami":
            if hazard_demand_type == "momentumflux":
                hazard_demand_type = "mmax"
            elif hazard_demand_type == "inundationdepth":
                hazard_demand_type = "hmax"

        return hazard_demand_type


/*******************************************************************************
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * Contributors:
 *     Shawn Hampton, Jong Lee, Chris Navarro, Nathan Tolbert (NCSA) - initial API and implementation and/or initial documentation
 *******************************************************************************/
package edu.illinois.ncsa.ergo.eq.buildings.tasks;

import java.io.IOException;
import java.util.HashMap;
import java.util.Map;

import javax.swing.table.DefaultTableModel;

import ncsa.tools.elf.core.exceptions.ScriptExecutionException;

import org.eclipse.core.runtime.IProgressMonitor;
import org.geotools.data.simple.SimpleFeatureCollection;
import org.geotools.data.simple.SimpleFeatureIterator;
import org.opengis.feature.simple.SimpleFeature;

import edu.illinois.ncsa.ergo.core.analysis.ogrescript.tasks.core.SimpleFeatureTask;
import edu.illinois.ncsa.ergo.eq.buildings.Building;
import edu.illinois.ncsa.ergo.eq.buildings.BuildingNonStructuralDamage;
import edu.illinois.ncsa.ergo.gis.datasets.FeatureDataset;
import edu.illinois.ncsa.ergo.gis.datasets.TableDataset;
import edu.illinois.ncsa.ergo.gis.util.FeatureUtils;

/**
 * @author
 *
 *         TODO add class documentation and license header
 */
public class BuildingDirectEconomicDamageTask extends SimpleFeatureTask
{
	// private final org.apache.log4j.Logger logger =
	// org.apache.log4j.Logger.getLogger( this.getClass() );

	private FeatureDataset buildingNSContentDamageV4;
	private TableDataset occupancyDamageMultipliers;
	private TableDataset inflationTable;
	// private TableDataset assessmentTable;
	private double defaultInflationFactor;
	private Map<String, BuildingNonStructuralDamage> nonStructuralDamageMap = new HashMap<String, BuildingNonStructuralDamage>();

	private double str_loss;
	private double str_loss_dev;
	private double acc_loss;
	private double acc_loss_dev;
	private double dri_loss;
	private double dri_loss_dev;
	private double con_loss;
	private double con_loss_dev;
	private double tot_loss;
	private double tot_loss_dev;

	/**
	 *
	 */
	protected void preProcess()
	{
		str_loss = 0.0;
		str_loss_dev = 0.0;
		acc_loss = 0.0;
		acc_loss_dev = 0.0;
		dri_loss = 0.0;
		dri_loss_dev = 0.0;
		con_loss = 0.0;
		con_loss_dev = 0.0;
		tot_loss = 0.0;
		tot_loss_dev = 0.0;
		if (buildingNSContentDamageV4 != null) {
			if (nonStructuralDamageMap.size() == 0) {
				populateFeatureMap(nonStructuralDamageMap, buildingNSContentDamageV4);
				// logger.warn("map size = "+nonStructuralDamageMap.size());
			}
		}
	}

	/**
	 *
	 * @param monitor
	 * @ScriptExecutionException
	 */
	protected void handleFeature(IProgressMonitor monitor) throws ScriptExecutionException
	{
		int appraised_val_col = feature.getFeatureType().indexOf(Building.APPRAISED_VALUE);
		int occ_type_col = feature.getFeatureType().indexOf(Building.OCCUPANCY_TYPE);
		String guid = null;

		int bldgIdCol = feature.getFeatureType().indexOf(Building.BUILDING_ID_COL);
		if (bldgIdCol != -1) {
			guid = (String) feature.getAttribute(bldgIdCol);
		} else {
			guid = (String) feature.getAttribute(FeatureDataset.FEATURE_GUID);
		}

		double inflationMultiplier = getInflationMultiplier();
		if (appraised_val_col != -1 && occ_type_col != -1) {
			String occtype = (String) feature.getAttribute(occ_type_col);
			double appraisedValue = getAppraisedValue(occtype, appraised_val_col);

			double mean_damage = (Double) feature.getAttribute(Building.MEAN_DAMAGE);
			double mean_damage_dev = (Double) feature.getAttribute(Building.MEAN_DAMAGE_DEV);
			double strDmgMultiplier = getMultiplier(occtype, 0);

			BuildingNonStructuralDamage nonStructuralDmgFeature = findFeature(nonStructuralDamageMap, guid);

			if (nonStructuralDmgFeature != null) {
				str_loss = this.computeEconomicLoss(strDmgMultiplier, mean_damage, appraisedValue, inflationMultiplier);
				str_loss_dev = this.computeStandardDeviationEconomicLoss(strDmgMultiplier, mean_damage_dev, appraisedValue,
						inflationMultiplier);

				// Acceleration sensitive NS damage loss
				mean_damage = nonStructuralDmgFeature.getMeanDamageAS();
				mean_damage_dev = nonStructuralDmgFeature.getMeanDamageDevAS();
				double as_nonStrDmgMultiplier = this.getMultiplier(occtype, 1);
				acc_loss = this.computeEconomicLoss(as_nonStrDmgMultiplier, mean_damage, appraisedValue, inflationMultiplier);
				acc_loss_dev = this.computeStandardDeviationEconomicLoss(as_nonStrDmgMultiplier, mean_damage_dev, appraisedValue,
						inflationMultiplier);

				// Drift sensitive NS damage loss
				mean_damage = nonStructuralDmgFeature.getMeanDamageDS();
				mean_damage_dev = nonStructuralDmgFeature.getMeanDamageDevDS();
				double ds_nonStrDmgMultiplier = this.getMultiplier(occtype, 2);
				dri_loss = this.computeEconomicLoss(ds_nonStrDmgMultiplier, mean_damage, appraisedValue, inflationMultiplier);
				dri_loss_dev = this.computeStandardDeviationEconomicLoss(ds_nonStrDmgMultiplier, mean_damage_dev, appraisedValue,
						inflationMultiplier);

				// Content Damage Loss
				mean_damage = nonStructuralDmgFeature.getMeanDamageContent();
				mean_damage_dev = nonStructuralDmgFeature.getMeanDamageDevContent();
				double content_nonStrDmgMultiplier = this.getMultiplier(occtype, 3);
				con_loss = this.computeEconomicLoss(content_nonStrDmgMultiplier, mean_damage, appraisedValue, inflationMultiplier);
				con_loss_dev = this.computeStandardDeviationEconomicLoss(content_nonStrDmgMultiplier, mean_damage_dev, appraisedValue,
						inflationMultiplier);
			} else {
				// It was determined after some email exchange with Steve French
				// that if the user does not supply non-structural damage
				// we should compute str_loss from the entire appraised value
				str_loss = this.computeEconomicLoss(1.0, mean_damage, appraisedValue, inflationMultiplier);
				str_loss_dev = this.computeStandardDeviationEconomicLoss(1.0, mean_damage_dev, appraisedValue, inflationMultiplier);
			}

			tot_loss = str_loss + acc_loss + dri_loss + con_loss;
			tot_loss_dev = Math.sqrt(Math.pow(str_loss_dev, 2) + Math.pow(acc_loss_dev, 2) + Math.pow(dri_loss_dev, 2)
					+ Math.pow(con_loss_dev, 2));

		}

		resultMap.put(Building.STR_LOSS_FIELD, str_loss);
		resultMap.put(Building.STR_LOSS_DEV_FIELD, str_loss_dev);
		resultMap.put(Building.ACC_LOSS_FIELD, acc_loss);
		resultMap.put(Building.ACC_LOSS_DEV_FIELD, acc_loss_dev);
		resultMap.put(Building.DRI_LOSS_FIELD, dri_loss);
		resultMap.put(Building.DRI_LOSS_DEV_FIELD, dri_loss_dev);
		resultMap.put(Building.CON_LOSS_FIELD, con_loss);
		resultMap.put(Building.CON_LOSS_DEV_FIELD, con_loss_dev);
		resultMap.put(Building.TOT_LOSS_FIELD, tot_loss);
		resultMap.put(Building.TOT_LOSS_DEV_FIELD, tot_loss_dev);
	}

	/**
	 *
	 * @param occtype
	 * @param appraised_val_col
	 * @return
	 */
	private double getAppraisedValue(String occtype, int appraised_val_col)
	{
		double assessedValue = Double.parseDouble(feature.getAttribute(appraised_val_col).toString());
		double appraisedValue = assessedValue; /*
												 * / getAssessmentRate( occtype
												 * );
												 */
		return appraisedValue;
	}

	/*
	 * Once we find out whether we have assessed or appraised values we can
	 * either remove this code or uncomment it private double getAssessmentRate(
	 * String occtype ) { if ( assessmentTable != null ) { DefaultTableModel
	 * tableModel = assessmentTable.getTableModel(); int occTableCol =
	 * assessmentTable.findColumn( "occupancy" ); int assessmentCol =
	 * assessmentTable.findColumn( "asses_rate" );
	 *
	 * for ( int row = 0; row < tableModel.getRowCount(); row++ ) { String
	 * rowOccType = (String)tableModel.getValueAt( row, occTableCol );
	 * if(rowOccType.equalsIgnoreCase( occtype )) { double assessmentRate =
	 * Double.parseDouble( tableModel.getValueAt( row, assessmentCol
	 * ).toString() ); if(assessmentRate == 0.0) { assessmentRate = 1.0; } else
	 * { return assessmentRate / 100.0; }
	 *
	 * } } } return 1.0; }
	 */

@staticmethod
getAppraisedValue

    @staticmethod
    def get_inflation_multiplier():
        """Get inflation multiplier.

        Args:
            feature_map (BuildingNonStructuralDamage): feature_map
            guid (str): guid.

        Returns:
            float: locatedFeature.

        """
        # private class variable
        defaultInflationFactor = 0

        # int taxAssessYearCol = feature.getFeatureType().indexOf(Building.APPRAISAL_DATE_COL);
		# if (inflationTable != null) {
		# 	DefaultTableModel tableModel = inflationTable.getTableModel();
		# 	double oldCPI = 0.0;
		# 	double newCPI = 0.0;
		# 	int yearCol = inflationTable.findColumn("year");
		# 	int cpiCol = inflationTable.findColumn("cpi");
        #
		# 	int taxYear = 2005;
        #
		# 	if (taxAssessYearCol != -1) {
		# 		taxYear = (Integer) feature.getAttribute(taxAssessYearCol);
		# 	}
		# 	for (int row = 0; row < tableModel.getRowCount(); row++) {
		# 		int rowYear = Integer.parseInt(tableModel.getValueAt(row, yearCol).toString());
		# 		if (rowYear == taxYear) {
		# 			oldCPI = Double.parseDouble(tableModel.getValueAt(row, cpiCol).toString());
		# 			newCPI = Double.parseDouble(tableModel.getValueAt(tableModel.getRowCount() - 1, cpiCol).toString());
		# 			double inflation = (newCPI - oldCPI) / oldCPI;
		# 			return (inflation + 1);
		# 		}
		# 	}
        #
		# 	return (1.0 + defaultInflationFactor / 100.0);
        #
		# } else {
		# 	return (1.0 + defaultInflationFactor / 100.0);
		# }

        return (1.0 + defaultInflationFactor / 100.0)

    @staticmethod
    def findFeature(feature_map, guid):
        """Calculates multiplier.

        Args:
            feature_map (BuildingNonStructuralDamage): feature_map
            guid (str): guid.

        Returns:
            float: locatedFeature.

        """
        nsDamage = None

        # 		if (featureDataset == null)
        # 			return;
        #
        # 		SimpleFeatureCollection fc = null;
        # 		SimpleFeatureIterator iterator = null;
        # 		try {
        # 			fc = featureDataset.getFeatures();
        # 			iterator = fc.features();
        #
        # 			while (iterator.hasNext()) {
        # 				SimpleFeature nsfeature = iterator.next();
        # 				int bldgIdCol = nsfeature.getFeatureType().indexOf(Building.BUILDING_ID_COL);
        # 				int guid_col = nsfeature.getFeatureType().indexOf(FeatureDataset.FEATURE_GUID);
        # 				int meanDamageASCol = FeatureUtils.findColumn(nsfeature, Building.MEAN_DMG_AS);
        # 				int meanDamageDevASCol = FeatureUtils.findColumn(nsfeature, Building.MEAN_DMG_DEV_AS);
        # 				int meanDamageDSCol = FeatureUtils.findColumn(nsfeature, Building.MEAN_DMG_DS);
        # 				int meanDamageDevDSCol = FeatureUtils.findColumn(nsfeature, Building.MEAN_DMG_DEV_DS);
        # 				int meanDamageContentCol = FeatureUtils.findColumn(nsfeature, Building.MEAN_DMG_CONTENT);
        # 				int meanDamageDevContentCol = FeatureUtils.findColumn(nsfeature, Building.MEAN_DMG_DEV_CONTENT);
        #
        # 				String ns_damage_feature_guid = null;
        # 				if (bldgIdCol != -1) {
        # 					ns_damage_feature_guid = (String) nsfeature.getAttribute(bldgIdCol);
        # 				} else {
        # 					ns_damage_feature_guid = (String) nsfeature.getAttribute(guid_col);
        # 				}
        #
        # 				BuildingNonStructuralDamage nsDamage = new BuildingNonStructuralDamage();
        #
        # 				double meanDamageAS = (Double) nsfeature.getAttribute(meanDamageASCol);
        # 				nsDamage.setMeanDamageAS(meanDamageAS);
        #
        # 				double meanDamageDevAS = (Double) nsfeature.getAttribute(meanDamageDevASCol);
        # 				nsDamage.setMeanDamageDevAS(meanDamageDevAS);
        #
        # 				double meanDamageDS = (Double) nsfeature.getAttribute(meanDamageDSCol);
        # 				nsDamage.setMeanDamageDS(meanDamageDS);
        #
        # 				double meanDamageDevDS = (Double) nsfeature.getAttribute(meanDamageDevDSCol);
        # 				nsDamage.setMeanDamageDevDS(meanDamageDevDS);
        #
        # 				double meanDamageContent = (Double) nsfeature.getAttribute(meanDamageContentCol);
        # 				nsDamage.setMeanDamageContent(meanDamageContent);
        #
        # 				double meanDamageDevContent = (Double) nsfeature.getAttribute(meanDamageDevContentCol);
        # 				nsDamage.setMeanDamageDevContent(meanDamageDevContent);
        #
        # 				// if(!featureMap.containsKey( ns_damage_feature_guid )) {
        # 				featureMap.put(ns_damage_feature_guid, nsDamage);
        # 				// } //else {
        # 				// logger.warn( "we already have this feature in the map!" );
        # 				// }
        # 			}
        # 		} catch (IOException e) {
        # 			error("Can't access the feature collection to build the map from.", e);
        # 		} catch (OutOfMemoryError e) {
        # 			warning("We ran out of memory building the non-structural damage map so we are proceeding without this performance tweak");
        # 		} finally {
        # 			iterator.close();
        # 		}
        return nsDamage


    @staticmethod
    def find_feature(featureDataset, guid):
        """Calculates multiplier.

        Args:
            featureDataset (FeatureDataset): featureDataset
            guid (str): guid.

        Returns:
            float: locatedFeature.

        """
        locatedFeature = None

        # if (featureDataset == null)
		# 	return locatedFeature;
        #
		# SimpleFeatureCollection fc = null;
		# try {
		# 	fc = featureDataset.getFeatures();
		# } catch (IOException e) {
		# 	error("Can't access the feature collection to build the map from.", e);
		# 	return locatedFeature;
		# }
        #
		# SimpleFeatureIterator iterator = fc.features();
        #
		# try {
		# 	boolean found = false;
		# 	while (iterator.hasNext() && !found) {
		# 		SimpleFeature feature = iterator.next();
		# 		int guid_col = feature.getFeatureType().indexOf(FeatureDataset.FEATURE_GUID);
		# 		int bldgIdCol = feature.getFeatureType().indexOf(Building.BUILDING_ID_COL);
        #
		# 		if (bldgIdCol != -1) {
		# 			String ns_damage_feature_guid = (String) feature.getAttribute(bldgIdCol);
		# 			if (ns_damage_feature_guid.equals(guid)) {
		# 				locatedFeature = feature;
		# 				found = true;
		# 			}
		# 		} else if (guid_col != -1) {
		# 			String ns_damage_feature_guid = (String) feature.getAttribute(guid_col);
		# 			if (ns_damage_feature_guid.equals(guid)) {
		# 				locatedFeature = feature;
		# 				found = true;
		# 			}
        #
		# 		}
		# 	}
		# } finally {
		# 	iterator.close()
		# }

        return locatedFeature


    @staticmethod
    def get_multiplier(occType, type):
        """Calculates multiplier.

        Args:
            occType (str): Occupancy Class (RES1, RES2, etc).
            type (int): 0 - Structural damage multiplier
                        1 - AS damage multiplier
                        2 - DS damage multiplier
                        3 - Content damage multiplier
        Returns:
            float: Multiplier.

        """
        # DefaultTableModel t = occupancyDamageMultipliers.getTableModel()
        # for (int i = 0; i < t.getRowCount(); i++) {
        #     occupancy = (String) t.getValueAt(i, 0)
        #     if (occupancy.equalsIgnoreCase(occType))
        #         return Double.parseDouble((String) t.getValueAt(i, type + 1)) / 100.0
        return 0

    @staticmethod
    def compute_economic_loss(multiplier, mean, appraised_val, inflation_multiplier):
        """Calculates economic loss.

        Args:
            multiplier (float): A multiplier.
            mean (float): A mean damage dev.
            appraised_val (float): A building apraised value.
            inflation_multiplier (float): An inflation multiplier.

        Returns:
            float: Economic loss.

        """
        return multiplier * mean * appraised_val * inflation_multiplier

    @staticmethod
    def compute_deviation_loss(multiplier, mean, appraised_val, inflation_multiplier):
        """Calculates standard deviation economic loss.

        Args:
            multiplier (float): A multiplier.
            mean (float): A mean damage dev.
            appraised_val (float): A building apraised value.
            inflation_multiplier (float): An inflation multiplier.

        Returns:
            float: Economic loss.

        """
        return multiplier * mean * appraised_val * inflation_multiplier

# nonStructuralDamage
#
# this.buildingNSContentDamageV4 = nonStructuralDamage
#
# occupancyDamageMultipliers
# inflationTable
# assessmentTable
# defaultInflationFactor


