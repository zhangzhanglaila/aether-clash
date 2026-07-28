from equipment_data import HERO_RECOMMENDED_ITEMS, ITEMS
from game_data import dist


class EconomyMixin:
    def near_shop(self):
        home_core = self.blue_core if self.player.team == "blue" else self.red_core
        return self.player.alive and dist(self.player, home_core) <= 155


    def buy_item(self, item_key):
        if self.state != "playing":
            return False
        if not self.near_shop():
            self.show_message(self.text("need_base"))
            return False
        item = ITEMS[item_key]
        current_level = self.player.equipment[item_key]
        if current_level >= item["max_stacks"]:
            self.show_message(self.text("item_max"))
            return False
        missing_item = self.missing_item_requirement(self.player, item)
        if missing_item:
            self.show_message(self.text("need_component", item=self.item_name(missing_item)))
            return False
        cost = item["cost"] + current_level * 70
        if self.player.gold < cost:
            self.show_message(self.text("not_enough_gold"))
            return False

        self.player.gold -= cost
        self.player.equipment[item_key] += 1
        if "attack_damage" in item:
            self.player.attack_damage += item["attack_damage"]
        if "skill_power" in item:
            self.player.skill_power += item["skill_power"]
        if "speed" in item:
            self.player.speed += item["speed"]
        if "attack_range" in item:
            self.player.attack_range += item["attack_range"]
        if "attack_cd_reduce" in item:
            self.player.attack_cd = max(0.2, self.player.attack_cd - item["attack_cd_reduce"])
        if "max_hp" in item:
            self.player.max_hp += item["max_hp"]
            self.player.hp += item["max_hp"]
        self.show_message(self.text("bought", item=self.item_name(item_key)))
        return True


    def missing_item_requirement(self, hero, item):
        for required_key, required_level in item.get("requires", {}).items():
            if hero.equipment.get(required_key, 0) < required_level:
                return required_key
        return None


    def buy_recommended_item(self):
        recommended = HERO_RECOMMENDED_ITEMS.get(self.player.hero_key, [])
        for item_key in recommended:
            item = ITEMS[item_key]
            if self.player.equipment.get(item_key, 0) >= item["max_stacks"]:
                continue
            missing_item = self.missing_item_requirement(self.player, item)
            candidate = missing_item or item_key
            if self.player.equipment.get(candidate, 0) >= ITEMS[candidate]["max_stacks"]:
                continue
            self.buy_item(candidate)
            return True
        self.show_message(self.text("no_recommended"))
        return True

