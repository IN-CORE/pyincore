#### 4.2. Computing expected economic losses

class BuildingEconDamage():
    def damage(self):
        damage_factor_mean = [0.005, 0.155, 0.55, 0.90]  # from MAEVIS documentation
        rt = [100, 250, 500, 1000, 2500, 5000, 10000]

        # reading in rmv values of each building
        bldg_dmg = BuildingDamage(client)  # initializing pyincore
        bldg_dataset_id = "5df40388b9219c06cf8b0c80"
        bldg_dmg.load_remote_input_dataset("buildings", bldg_dataset_id)
        dataset = bldg_dmg.input_datasets["buildings"]["value"]
        rd = dataset.get_inventory_reader()

        rmv = []
        for row in rd:
            rmv.append(row["properties"]["rmv_improv"])

        # storing rmv data in each dataframe
        data_eq_store["rmv"] = rmv
        data_tsu_store["rmv"] = rmv
        data_cumulative_store["rmv"] = rmv

        loss_eq_tot = []
        loss_tsu_tot = []
        loss_cumulative_tot = []

        for rt_val in rt:
            loss_insg = data_eq_store["rmv"] * data_eq_store["insignific_{}".format(rt_val)] * damage_factor_mean[0]
            loss_modr = data_eq_store["rmv"] * data_eq_store["moderate_{}".format(rt_val)] * damage_factor_mean[1]
            loss_heav = data_eq_store["rmv"] * data_eq_store["heavy_{}".format(rt_val)] * damage_factor_mean[2]
            loss_comp = data_eq_store["rmv"] * data_eq_store["complete_{}".format(rt_val)] * damage_factor_mean[3]
            loss_eq = loss_insg + loss_modr + loss_heav + loss_comp

            loss_insg = data_tsu_store["rmv"] * data_tsu_store["insignific_{}".format(rt_val)] * damage_factor_mean[0]
            loss_modr = data_tsu_store["rmv"] * data_tsu_store["moderate_{}".format(rt_val)] * damage_factor_mean[1]
            loss_heav = data_tsu_store["rmv"] * data_tsu_store["heavy_{}".format(rt_val)] * damage_factor_mean[2]
            loss_comp = data_tsu_store["rmv"] * data_tsu_store['"complete_{}".format(rt_val)] * damage_factor_mean[3]
            loss_tsu = loss_insg + loss_modr + loss_heav + loss_comp

            loss_insg = data_cumulative_store["rmv"] * data_cumulative_store["insignific_{}".format(rt_val)] * damage_factor_mean[0]
            loss_modr = data_cumulative_store["rmv"] * data_cumulative_store["moderate_{}".format(rt_val)] * damage_factor_mean[1]
            loss_heav = data_cumulative_store["rmv"] * data_cumulative_store["heavy_{}".format(rt_val)] * damage_factor_mean[2]
            loss_comp = data_cumulative_store["rmv"] * data_cumulative_store["complete_{}".format(rt_val)] * damage_factor_mean[3]
            loss_cumulative = (loss_insg + loss_modr + loss_heav + loss_comp)

            loss_eq_tot.append(loss_eq.sum())
            loss_tsu_tot.append(loss_tsu.sum())
            loss_cumulative_tot.append(loss_cumulative.sum())

        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        ax.plot(rt, loss_eq_tot, "b", ls="-")
        ax.plot(rt, loss_tsu_tot, "r", ls="-")
        ax.plot(rt, loss_cumulative_tot, "k", ls="-")

        ax.set_xlabel("Return Period (years)")
        ax.set_ylabel("Economic Losses ($)")
        ax.set_title("Economic Losses")

        ax.set_xscale("log")
        ax.grid(which="minor", alpha=0.25, color="k", ls=":")
        ax.grid(which="major", alpha=0.40, color="k", ls="--")

        #### 4.3. Computing expected economic risks
        # Risks are defined as losses times probability of occurrence (or the inverserse of the return period). With economic risks, one can isolate events that result in both large economic losses, as well as have a high probability of occurrence.

        fig, ax = plt.subplots(1,1, figsize=(12,8))

        risk_eq = [l/r for l,r in zip(loss_eq_tot, rt)]
        risk_tsu = [l/r for l,r in zip(loss_tsu_tot, rt)]
        risk_cumulative = [l/r for l,r in zip(loss_cumulative_tot, rt)]

        ax.plot(rt, risk_eq, "b", ls="-")
        ax.plot(rt, risk_tsu, "r", ls="-")
        ax.plot(rt, risk_cumulative, "k", ls="-")

        ax.set_xlabel("Return Period (years)")
        ax.set_ylabel("Risk")
        ax.set_title("Economic Risks")

        ax.set_xscale("log")
        ax.grid(which="minor", alpha=0.25, color = "k", ls = ":")
        ax.grid(which="major", alpha=0.40, color = "k", ls = "--")
