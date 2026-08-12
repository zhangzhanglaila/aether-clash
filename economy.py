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
        self.add_match_stat(self.player.team, "items_spent", cost)
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
        gain_text = self.item_gain_text(item)
        if gain_text:
            self.spawn_floating_text(self.player.x, self.player.y - 72, gain_text, item["color"], ttl=1.05)
            self.spawn_particles(self.player.x, self.player.y, item["color"], count=12, speed=95, spread=0.9, radius=2.4, ttl=0.28)
        return True


    def item_gain_text(self, item):
        parts = []
        if item.get("attack_damage"):
            parts.append(f"+{item['attack_damage']} {self.text('stat_attack')}")
        if item.get("skill_power"):
            parts.append(f"+{item['skill_power']} {self.text('stat_skill')}")
        if item.get("max_hp"):
            parts.append(f"+{item['max_hp']} {self.text('stat_hp')}")
        if item.get("speed"):
            parts.append(f"+{item['speed']} {self.text('stat_speed')}")
        if item.get("attack_range"):
            parts.append(f"+{item['attack_range']} {self.text('stat_range')}")
        if item.get("attack_cd_reduce"):
            parts.append(f"+{int(item['attack_cd_reduce'] * 100)} {self.text('stat_haste')}")
        passive_key = item.get("passive")
        if passive_key:
            parts.append(self.text(f"passive_{passive_key}"))
        return " / ".join(parts[:3])


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

