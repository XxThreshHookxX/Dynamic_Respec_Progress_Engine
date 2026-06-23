# ==============================================================================
#  PROJECT:   Dynamic Respec Progress Engine
#  CONCEPT:   Calculator used to optimize the progress of individual players.
#  REVISION:  Version 0.1.1 corrected title loop count and tracker
#             V0.2.1 added movespeed calculations with 4 minute threshhold
#             v0.2.2 added atr threshholds and implication to contribute monster spawn to pixel max vs the damage increment in each speed manager
#             v0.2.3 added logic to save skill points for movement if past a 4 minute thresh and added a logic stop to anyone with resets that are 40k+ halting at 40k like manager does.
#             v0.2.3.1 updated variables to be user friendly and added an absolute to run time (thank you Gebous)
#             V0.2.3.2 Adjusted max run tim to be a +20 luck corrected percentage to showcase total invested not based on avaiable.
#             V0.2.3.3 Finalized run time adjustments and adjusted values for more realistic runs
#             V0.3     added a pre 5k loop stooped unauthorized values from input.
#             V0.3.1   corrected logic breaks in the math to prevet malicious intent and idiot proofing the code, put limits on variables.
#             V0.3.2   corrected loop logic with standard and absolute mixing up at certain break points.
#             V0.3.3   corrected the dynamic application of titles to apply an ROI based on acct value.
#             V0.4     cleaned up code corrected logic points and removed unused code.
#  CREDITS:   Core Logic, infrastructure coding etc. by JMcQueen
#             Math and progress formulas contributed by Bach and Fierywind
# ==============================================================================

import sys
import math

# Safeguards the application from evaluation bugs if executed in Python 2
if sys.version_info < (3, 0):
    print("[-] Critical Error: This system engine requires Python 3 or higher to run safely.")
    sys.exit(1)


def calculate_bracket_costs(starting_stat_level, total_levels_to_purchase):
    """Calculates the scaling skill point cost across flat 10-level increments."""
    total_skill_point_cost = 0
    for level_index in range(total_levels_to_purchase):
        active_level = starting_stat_level + level_index
        total_skill_point_cost += int(active_level // 10) + 1
    return total_skill_point_cost


def find_next_title_milestone(current_total_sword_level):
    """Snaps to clean 150-level title milestone lines."""
    stage_remainder = current_total_sword_level % 150
    if stage_remainder == 0:
        return current_total_sword_level + 150
    return current_total_sword_level + (150 - stage_remainder)

def get_milestone_utility_worth(target_title_milestone, player_vip_tier, player_account_level, total_raw_swords_purchased):
    """Calculates the flat stage progress value assigned to major milestone title rushes based on account values."""
    title_index = int(target_title_milestone // 150)
    cycle_progression_position = title_index % 3  

    # Exact game multipliers: 2x, 3x, 4x, 5x, 6x, and 10x
    vip_package_multipliers = [2.0, 3.0, 4.0, 5.0, 6.0, 10.0]
    base_multiplier_pool = vip_package_multipliers[max(0, min(int(player_vip_tier), 5))]

    root_step_progression_modifier = math.pow(base_multiplier_pool, 1.0 / 450.0)
    
    # Baseline fallback weights
    stat_weight_factor = 1.0  
    
    # Cycles every title: 1=Damage (1.0), 2=Gold (Dynamic), 0=XP (Dynamic)
    if cycle_progression_position == 2:
        # Gold increase per level marginal ROI calculation
        current_gold = round(10.0 * total_raw_swords_purchased * math.pow(1.0002, total_raw_swords_purchased), 0)
        previous_swords = max(1.0, total_raw_swords_purchased - 1.0)
        previous_gold = round(10.0 * previous_swords * math.pow(1.0002, previous_swords), 0)
        
        gold_roi_ratio = (current_gold / previous_gold) if previous_gold > 0 else 1.0
        # Normalizes the ratio against the baseline 0.50 game weight layout
        stat_weight_factor = 0.50 * gold_roi_ratio
        
    elif cycle_progression_position == 0:
        # XP increase per level marginal ROI calculation
        current_xp = round(((100.0 + (50.0 * player_account_level)) / 2.0 * player_account_level) * math.pow(1.003, player_account_level), 0)
        previous_level = max(1.0, player_account_level - 1.0)
        previous_xp = round(((100.0 + (50.0 * previous_level)) / 2.0 * previous_level) * math.pow(1.003, previous_level), 0)
        
        xp_roi_ratio = (current_xp / previous_xp) if previous_xp > 0 else 1.0
        # Normalizes the ratio against the baseline 0.35 game weight layout
        stat_weight_factor = 0.35 * xp_roi_ratio
        
    return (math.log(root_step_progression_modifier) / math.log(1.014)) * stat_weight_factor


def compute_monsters_in_range(starting_run_stage, final_target_stage, speed_manager_level):
    """Calculates the absolute monster density on specific stages landed on by the speed manager."""
    total_monsters_encountered = 0
    standard_boss_intervals = list((10, 20, 30, 40, 60, 70, 80, 90))
    
    for current_stage in range(int(starting_run_stage), int(final_target_stage) + 1, int(speed_manager_level)):
        hundreds_remainder = current_stage % 100
        
        if hundreds_remainder == 0:
            total_monsters_encountered += 50
        elif hundreds_remainder == 50:
            total_monsters_encountered += 30
        elif hundreds_remainder in standard_boss_intervals:
            total_monsters_encountered += 20
        else:
            total_monsters_encountered += 10
            
    return total_monsters_encountered


def calculate_range_penalty_factor(current_attack_range_stats):
    """Applies a clearing duration penalty factor if the player is under 215 Attack Range."""
    if current_attack_range_stats >= 215.0:
        return 1.0
    else:
        return 1.0 + ((215.0 - current_attack_range_stats) * 0.01)


def calculate_range_stage_worth(current_attack_range_stats):
    """Converts the attack range wave clearing brackets into flat stage progress values."""
    if current_attack_range_stats >= 435.0:
        return 11.0
    elif current_attack_range_stats >= 215.0:
        return 5.5
    else:
        return 1.0


def get_validated_input(prompt_message, allow_zero=False, max_limit=10000000):
    """Rejects special float values like NaN/Infinity and enforces a 10M safe processing ceiling."""
    while True:
        try:
            raw_input = input(prompt_message).strip()
            if raw_input.lower() in ["nan", "inf", "-inf", "infinity"]:
                print("[-] Security Alert: Special floating-point literals are strictly prohibited.")
                continue
                
            user_value = float(raw_input)
            
            if not math.isfinite(user_value):
                print("[-] Security Alert: Input must be a finite numerical value.")
                continue
            if user_value > max_limit:
                print(f"[-] Security Alert: Input exceeds safe processing maximum of {max_limit:,}.")
                continue
            if allow_zero and user_value >= 0:
                return user_value
            elif not allow_zero and user_value > 0:
                return user_value
            print("[-] Error: Invalid value. This specific setting must be greater than 0.")
        except ValueError:
            print("[-] Error: Input verification failed. Numbers only. Please try again.")
def run_allocation_simulation(spendable_skill_points_pool, current_sword_skill_points, total_sword_with_gear, player_vip_tier, 
                              base_clear_speed, total_floors_visited, current_attack_range, target_range_threshold, 
                              speed_manager_level, max_stage_reached, player_account_level, total_raw_swords_purchased, optimization_mode="standard"):
    """Closed-loop strategy engine resolving point distribution across priority weights."""
    remaining_skill_points = int(spendable_skill_points_pool)
    allocated_sword_level = int(current_sword_skill_points)
    allocated_damage_level = allocated_attack_speed_level = allocated_move_speed_level = allocated_attack_range_level = 0
    newly_added_damage_levels = newly_added_attack_speed_levels = newly_added_sword_levels = newly_added_move_speed_levels = newly_added_attack_range_levels = 0
    accumulated_milestone_stage_worth = 0.0

    while remaining_skill_points > 0:
        competing_allocation_options = []
        live_total_sword_level = total_sword_with_gear + (allocated_sword_level - current_sword_skill_points)
        adjusted_clear_speed = (base_clear_speed * speed_manager_level) / (1.0 + (allocated_move_speed_level * 0.05))
        calculated_attack_range = current_attack_range + (allocated_attack_range_level * 0.5)
        estimated_active_run_time = total_floors_visited * adjusted_clear_speed * calculate_range_penalty_factor(calculated_attack_range)

        current_sword_cost_total = allocated_sword_level * (allocated_sword_level + 1) // 2
        allowed_to_invest_sword = not (optimization_mode == "standard" and max_stage_reached < 5000 and current_sword_cost_total >= (spendable_skill_points_pool * 0.70))

        if optimization_mode == "standard":
            if target_range_threshold > 0 and calculated_attack_range < target_range_threshold:
                single_level_cost = calculate_bracket_costs(allocated_attack_range_level, 2)
                if single_level_cost <= remaining_skill_points:
                    competing_allocation_options.append({"type": "attack_range_single", "cost": single_level_cost, "efficiency_value_score": 999999.0, "count": 2})
            elif estimated_active_run_time > 240.0 and max_stage_reached >= 5000:
                single_level_cost = int(allocated_move_speed_level // 10) + 1
                if single_level_cost <= remaining_skill_points:
                    competing_allocation_options.append({"type": "move_speed_single", "cost": single_level_cost, "efficiency_value_score": 99999.0, "count": 1})
        
        if not competing_allocation_options and optimization_mode == "max_depth" and allowed_to_invest_sword:
            cost_for_sword_single = allocated_sword_level + 1
            if cost_for_sword_single <= remaining_skill_points:
                competing_allocation_options.append({"type": "sword_single", "cost": cost_for_sword_single, "efficiency_value_score": 9999999.0, "count": 1})

        if not competing_allocation_options:
            cost_for_damage_block = calculate_bracket_costs(allocated_damage_level, 10)
            if cost_for_damage_block <= remaining_skill_points:
                damage_return_on_investment = math.log(((allocated_damage_level + 10) * 5 + 100) / (allocated_damage_level * 5 + 100)) / math.log(1.014)
                competing_allocation_options.append({"type": "damage_block", "cost": cost_for_damage_block, "efficiency_value_score": damage_return_on_investment / cost_for_damage_block, "count": 10})

            cost_for_attack_speed_block = calculate_bracket_costs(allocated_attack_speed_level, 10)
            if cost_for_attack_speed_block <= remaining_skill_points:
                attack_speed_return_on_investment = math.log(((allocated_attack_speed_level + 10) * 1 + 100) / (allocated_attack_speed_level * 1 + 100)) / math.log(1.014)
                competing_allocation_options.append({"type": "attack_speed_block", "cost": cost_for_attack_speed_block, "efficiency_value_score": attack_speed_return_on_investment / cost_for_attack_speed_block, "count": 10})

            if optimization_mode == "standard" and allowed_to_invest_sword:
                next_target_milestone = find_next_title_milestone(live_total_sword_level)
                required_levels_for_rush = next_target_milestone - live_total_sword_level
                cost_to_rush_milestone = sum((allocated_sword_level + 1 + level_offset) for level_offset in range(required_levels_for_rush))
                if 0 < cost_to_rush_milestone <= remaining_skill_points:
                    milestone_utility_worth = get_milestone_utility_worth(next_target_milestone, player_vip_tier, player_account_level, total_raw_swords_purchased)
                    competing_allocation_options.append({"type": "milestone_rush", "cost": cost_to_rush_milestone, "efficiency_value_score": ((required_levels_for_rush * 7.6267) + milestone_utility_worth) / cost_to_rush_milestone, "levels": required_levels_for_rush, "worth": milestone_utility_worth})

        if not competing_allocation_options or (remaining_skill_points < cost_for_damage_block and remaining_skill_points < cost_for_attack_speed_block and (not allowed_to_invest_sword or remaining_skill_points < cost_for_sword_single)):
            single_level_cost = int(allocated_damage_level // 10) + 1
            if single_level_cost <= remaining_skill_points:
                competing_allocation_options.append({"type": "damage_single", "cost": single_level_cost, "efficiency_value_score": (math.log(((allocated_damage_level + 1) * 5 + 100) / (allocated_damage_level * 5 + 100)) / math.log(1.014)) / single_level_cost, "count": 1})
            single_level_cost = int(allocated_attack_speed_level // 10) + 1
            if single_level_cost <= remaining_skill_points:
                competing_allocation_options.append({"type": "attack_speed_single", "cost": single_level_cost, "efficiency_value_score": (math.log(((allocated_attack_speed_level + 1) * 1 + 100) / (allocated_attack_speed_level * 1 + 100)) / math.log(1.014)) / single_level_cost, "count": 1})
            single_level_cost = int(allocated_move_speed_level // 10) + 1
            if single_level_cost <= remaining_skill_points:
                competing_allocation_options.append({"type": "move_speed_single", "cost": single_level_cost, "efficiency_value_score": 0.001 / single_level_cost, "count": 1})

        if not competing_allocation_options: break
        best_calculated_move = max(competing_allocation_options, key=lambda option: option["efficiency_value_score"])
        if best_calculated_move["cost"] > remaining_skill_points or best_calculated_move["cost"] <= 0: break
        remaining_skill_points -= best_calculated_move["cost"]

        if best_calculated_move["type"] in ["damage_block", "damage_single"]:
            allocated_damage_level += best_calculated_move["count"]; newly_added_damage_levels += best_calculated_move["count"]
        elif best_calculated_move["type"] in ["attack_speed_block", "attack_speed_single"]:
            allocated_attack_speed_level += best_calculated_move["count"]; newly_added_attack_speed_levels += best_calculated_move["count"]
        elif best_calculated_move["type"] == "sword_single":
            allocated_sword_level += best_calculated_move["count"]; newly_added_sword_levels += best_calculated_move["count"]
            if (total_sword_with_gear + (allocated_sword_level - current_sword_skill_points)) % 150 == 0:
                accumulated_milestone_stage_worth += get_milestone_utility_worth(total_sword_with_gear + (allocated_sword_level - current_sword_skill_points), player_vip_tier, player_account_level, total_raw_swords_purchased)
        elif best_calculated_move["type"] == "move_speed_single":
            allocated_move_speed_level += best_calculated_move["count"]; newly_added_move_speed_levels += best_calculated_move["count"]
        elif best_calculated_move["type"] == "attack_range_single":
            allocated_attack_range_level += best_calculated_move["count"]; newly_added_attack_range_levels += best_calculated_move["count"]
        elif best_calculated_move["type"] == "milestone_rush":
            allocated_sword_level += best_calculated_move["levels"]; newly_added_sword_levels += best_calculated_move["levels"]; accumulated_milestone_stage_worth += best_calculated_move["worth"]

    return {
        "damage_level": allocated_damage_level, "attack_speed_level": allocated_attack_speed_level, "move_speed_level": allocated_move_speed_level, 
        "attack_range_level": allocated_attack_range_level, "sword_spawn_level": allocated_sword_level, "leftover": remaining_skill_points, 
        "newly_added_damage": newly_added_damage_levels, "newly_added_attack_speed": newly_added_attack_speed_levels, "newly_added_sword_spawn": newly_added_sword_levels, 
        "newly_added_move_speed": newly_added_move_speed_levels, "newly_added_attack_range": newly_added_attack_range_levels, "milestone_worth": accumulated_milestone_stage_worth
    }
def print_simulation_results(simulation_title, configuration_dataset, spendable_skill_points_pool, current_sword_skill_points, initial_attack_range_radius, max_stage_reached, mode="standard"):
    """Outputs the complete respec strategy alongside the player's true cumulative point footprint matrix."""
    cost_for_damage_stat = calculate_bracket_costs(0, configuration_dataset['damage_level'])
    cost_for_attack_speed_stat = calculate_bracket_costs(0, configuration_dataset['attack_speed_level'])
    cost_for_move_speed_stat = calculate_bracket_costs(0, configuration_dataset['move_speed_level'])
    cost_for_attack_range_stat = calculate_bracket_costs(0, configuration_dataset['attack_range_level'])
    cost_for_sword_spawn_stat = configuration_dataset['sword_spawn_level'] * (configuration_dataset['sword_spawn_level'] + 1) // 2
    total_invested_character_budget = cost_for_damage_stat + cost_for_attack_speed_stat + cost_for_move_speed_stat + cost_for_attack_range_stat + cost_for_sword_spawn_stat

    p_dmg = (cost_for_damage_stat / total_invested_character_budget) * 100 if total_invested_character_budget > 0 else 0
    p_as = (cost_for_attack_speed_stat / total_invested_character_budget) * 100 if total_invested_character_budget > 0 else 0
    p_mv = (cost_for_move_speed_stat / total_invested_character_budget) * 100 if total_invested_character_budget > 0 else 0
    p_rng = (cost_for_attack_range_stat / total_invested_character_budget) * 100 if total_invested_character_budget > 0 else 0
    p_swd = (cost_for_sword_spawn_stat / total_invested_character_budget) * 100 if total_invested_character_budget > 0 else 0

    net_overall_stage_progress = int((configuration_dataset['newly_added_sword_spawn'] * 7.6267) + configuration_dataset['milestone_worth'] + (calculate_range_stage_worth(initial_attack_range_radius + (configuration_dataset['newly_added_attack_range'] * 0.5)) - calculate_range_stage_worth(initial_attack_range_radius)))

    print("\n" + "="*60)
    print(f"        {simulation_title}")
    if mode == "standard":
        print("        CORE SYSTEM ENGINE LOGIC BY: JMcQueen\n        BALANCING MATHEMATICS BY:    Bach & Fierywind")
    else:
        print("        Credits : JMcQueen")
    print("="*60)
    print(f" -> Optimal Target Damage Level:        {configuration_dataset['damage_level']} ({p_dmg:.2f}%)")
    print(f" -> Optimal Target Attack Speed Level:   {configuration_dataset['attack_speed_level']} ({p_as:.2f}%)")
    print(f" -> Optimal Target Move Speed Level:    {configuration_dataset['move_speed_level']} ({p_mv:.2f}%)")
    print(f" -> Optimal Target Attack Range Level:  {configuration_dataset['attack_range_level']} ({p_rng:.2f}%)")
    print(f" -> Final Expected Sword Skill Level:    {configuration_dataset['sword_spawn_level']} ({p_swd:.2f}%)")
    print(f" -> Remaining Unspent Spare Points:      {configuration_dataset['leftover']} SP")
    print(f" -> Estimated Target Stage Progress:    +{net_overall_stage_progress} stages gained")
    print("="*60)
    print("\n[+] CONSOLIDATED ALLOCATION ROADMAP:")
    step = 1
    if configuration_dataset['newly_added_sword_spawn'] > 0:
        print(f"Step {step}: Buy +{configuration_dataset['newly_added_sword_spawn']} levels in Sword Spawn (Target: Lvl {configuration_dataset['sword_spawn_level']})"); step += 1
    if configuration_dataset['newly_added_damage'] > 0:
        print(f"Step {step}: Buy +{configuration_dataset['newly_added_damage']} levels in Damage (Target: Lvl {configuration_dataset['damage_level']})"); step += 1
    if configuration_dataset['newly_added_attack_speed'] > 0:
        print(f"Step {step}: Buy +{configuration_dataset['newly_added_attack_speed']} levels in Attack Speed (Target: Lvl {configuration_dataset['attack_speed_level']})"); step += 1
    if configuration_dataset['newly_added_move_speed'] > 0:
        print(f"Step {step}: Buy +{configuration_dataset['newly_added_move_speed']} levels in Move Speed (Target: Lvl {configuration_dataset['move_speed_level']})"); step += 1
    if configuration_dataset['newly_added_attack_range'] > 0:
        print(f"Step {step}: Buy +{configuration_dataset['newly_added_attack_range']} levels in Attack Range (Target: Lvl {configuration_dataset['attack_range_level']})"); step += 1
    print(f"\n[+] Status complete. Balance remaining: {configuration_dataset['leftover']} SP.")


def execute_build_optimization(spendable_skill_points_pool, current_sword_skill_points, total_sword_with_gear, player_vip_tier, 
                               base_clear_speed, max_stage_reached, speed_manager_level, companion_multiplier_level, 
                               move_speed_base_stat, initial_attack_range_radius, target_range_threshold,
                               player_account_level, total_raw_swords_purchased):
    auto_reset_target_stage = int(max_stage_reached) if max_stage_reached < 5000 else min(40000, int(max_stage_reached * 0.80))
    starting_spawn_floor = int(max_stage_reached * 0.50) if max_stage_reached < 5000 else int(round((auto_reset_target_stage // 2) / 100.0) * 100)
    total_stages_to_run = auto_reset_target_stage - starting_spawn_floor
    
    companion_proc_chance = min(1.0, companion_multiplier_level * 0.0001)
    total_floors_visited_average = max(1.0, total_stages_to_run / (speed_manager_level + (companion_proc_chance * 100 * speed_manager_level)))
    net_monster_density_pool = compute_monsters_in_range(starting_spawn_floor, starting_spawn_floor + (total_floors_visited_average * speed_manager_level), speed_manager_level)
    
    true_seconds_per_room = base_clear_speed * speed_manager_level
    expected_average_run_time = total_floors_visited_average * true_seconds_per_room * calculate_range_penalty_factor(initial_attack_range_radius)
    total_floors_visited_worst_case = max(1.0, total_stages_to_run / speed_manager_level)
    absolute_longest_run_seconds = total_floors_visited_worst_case * true_seconds_per_room * calculate_range_penalty_factor(initial_attack_range_radius)
    absolute_fastest_run_seconds = max(1.0, total_stages_to_run / (speed_manager_level + (min(1.0, companion_proc_chance + 0.20) * 100 * speed_manager_level))) * true_seconds_per_room * calculate_range_penalty_factor(initial_attack_range_radius)

    print("\n" + "-"*60 + "\n        SPEED METRICS DIAGNOSTIC\n" + "-"*60)
    print(f" -> Starting Spawn Floor:               {starting_spawn_floor}\n -> Auto-Reset Target Stage:            {auto_reset_target_stage}")
    print(f" -> Expected Run Time (Average Skips):  {int(expected_average_run_time // 60)}m {round(expected_average_run_time % 60)}s ({expected_average_run_time:.2f}s)")
    print("-"*60)

    standard_build_profile = run_allocation_simulation(spendable_skill_points_pool, current_sword_skill_points, total_sword_with_gear, player_vip_tier, base_clear_speed, total_floors_visited_average, initial_attack_range_radius, target_range_threshold, speed_manager_level, max_stage_reached, player_account_level, total_raw_swords_purchased, optimization_mode="standard")
    maximum_depth_build_profile = run_allocation_simulation(spendable_skill_points_pool, current_sword_skill_points, total_sword_with_gear, player_vip_tier, base_clear_speed, total_floors_visited_average, initial_attack_range_radius, target_range_threshold, speed_manager_level, max_stage_reached, player_account_level, total_raw_swords_purchased, optimization_mode="max_depth")

    print_simulation_results("TARGET STRATEGY CONFIG RESULTS (STANDARD PROFILE)", standard_build_profile, spendable_skill_points_pool, current_sword_skill_points, initial_attack_range_radius, max_stage_reached, mode="standard")
    print_simulation_results("TARGET STRATEGY CONFIG RESULTS (ABSOLUTE MAXIMUM STAGE DEPTH PROFILE)", maximum_depth_build_profile, spendable_skill_points_pool, current_sword_skill_points, initial_attack_range_radius, max_stage_reached, mode="max_depth")


if __name__ == "__main__":
    print("============================================================\n       DYNAMIC RESPEC PROGRESS ENGINE\n============================================================")
    u_sp = int(get_validated_input("Enter total Spendable Skill Points Pool: ", allow_zero=True))
    u_ss = int(get_validated_input("Enter current Skill-Point Sword Level:   ", allow_zero=True))
    u_st = int(get_validated_input("Enter current Total Sword Level (w/ Gear): ", allow_zero=False))
    u_vip = int(get_validated_input("Enter Player VIP Title Level (0 through 5): ", allow_zero=True))
    u_bspd = float(get_validated_input("What is your recent fastest stage last 10 with no skill in move speed: ", allow_zero=False))
    u_maxs = int(get_validated_input("What is your max stage: ", allow_zero=False))
    u_smgr = int(get_validated_input("Enter your Speed Manager configuration level: ", allow_zero=False))
    u_comp = int(get_validated_input("Enter your stage-skipping Companion Level: ", allow_zero=True))
    u_mbase = float(get_validated_input("Enter total move speed from stats (no skill points allocated): ", allow_zero=False))
    u_crng = float(get_validated_input("Enter current total Attack Range (in stats): ", allow_zero=False))
    u_trng = float(get_validated_input("Enter target Attack Range Threshold to maintain (0, 215, or 435): ", allow_zero=True))
    u_plvl = int(get_validated_input("Enter your current Player Account Level: ", allow_zero=False))
    u_rswd = int(get_validated_input("Enter your total raw Swords Purchased across your account: ", allow_zero=False))

    execute_build_optimization(u_sp, u_ss, u_st, u_vip, u_bspd, u_maxs, u_smgr, u_comp, u_mbase, u_crng, u_trng, u_plvl, u_rswd)
