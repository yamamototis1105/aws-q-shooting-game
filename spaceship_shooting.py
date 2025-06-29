import pygame
import sys
import random
import math

# 初期化
pygame.init()

# 画面設定
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 1024
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Spaceship Shooting")

# 色の定義
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 100, 200)
LIGHT_BLUE = (100, 150, 255)
GREEN = (0, 200, 0)
LIGHT_GREEN = (100, 255, 100)
RED = (255, 0, 0)
ORANGE = (255, 165, 0)
YELLOW = (255, 255, 0)
PURPLE = (255, 0, 255)

# フォント設定
title_font = pygame.font.Font(None, 72)
button_font = pygame.font.Font(None, 48)
game_font = pygame.font.Font(None, 36)

class Player:
    def __init__(self):
        self.x = 50
        self.y = SCREEN_HEIGHT // 2
        self.width = 40
        self.height = 30
        self.speed = 5
        self.bullets = []
        self.last_shot = 0
        self.shot_delay = 200  # ミリ秒
        self.invincible = False  # 無敵状態
        self.shift_pressed = False  # Shiftキーの状態管理

    def update(self, keys_pressed, shift_key_event):
        if keys_pressed[pygame.K_UP] and self.y > 0:
            self.y -= self.speed
        if keys_pressed[pygame.K_DOWN] and self.y < SCREEN_HEIGHT - self.height:
            self.y += self.speed
        if keys_pressed[pygame.K_LEFT] and self.x > 0:
            self.x -= self.speed
        if keys_pressed[pygame.K_RIGHT] and self.x < SCREEN_WIDTH // 3:
            self.x += self.speed

        # Shiftキーでトグル式無敵状態
        if shift_key_event:
            self.invincible = not self.invincible

        # 弾を撃つ
        if keys_pressed[pygame.K_SPACE]:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_shot > self.shot_delay:
                self.bullets.append(Bullet(self.x + self.width, self.y + self.height // 2))
                self.last_shot = current_time

        # 弾の更新
        self.bullets = [bullet for bullet in self.bullets if bullet.update()]

    def draw(self, screen):
        # プレイヤーを描画（三角形の宇宙船）
        points = [
            (self.x + self.width, self.y + self.height // 2),
            (self.x, self.y),
            (self.x, self.y + self.height)
        ]

        # 無敵状態の時は色を変える
        color = LIGHT_BLUE if self.invincible else BLUE
        pygame.draw.polygon(screen, color, points)

        # 無敵状態の時はエフェクトを追加
        if self.invincible:
            pygame.draw.polygon(screen, WHITE, points, 2)

        # 弾を描画
        for bullet in self.bullets:
            bullet.draw(screen)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def is_invincible(self):
        return self.invincible

class Bullet:
    def __init__(self, x, y, speed=8, color=YELLOW):
        self.x = x
        self.y = y
        self.speed = speed
        self.color = color
        self.width = 8
        self.height = 4

    def update(self):
        self.x += self.speed
        return self.x < SCREEN_WIDTH

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

class Enemy:
    def __init__(self, x, y, enemy_type="red", formation_offset=0):
        self.x = x
        self.y = y
        self.enemy_type = enemy_type
        self.formation_offset = formation_offset
        self.bullets = []
        self.last_shot = 0
        self.time = 0

        if enemy_type == "red":
            self.width = 25
            self.height = 20
            self.speed = 2
            self.shot_delay = 2000  # 2秒間隔
            self.health = 1
        elif enemy_type == "orange":
            self.width = 30
            self.height = 30
            self.speed = 1.5
            self.shot_delay = 1500  # 1.5秒間隔
            self.health = 2
            self.zigzag_amplitude = 100
            self.zigzag_frequency = 0.02

    def update(self, player_x=None, player_y=None):
        self.time += 1

        if self.enemy_type == "red":
            # 赤い敵：直線移動
            self.x -= self.speed

            # 自機に向けて弾を撃つ
            if player_x is not None and player_y is not None:
                current_time = pygame.time.get_ticks()
                if current_time - self.last_shot > self.shot_delay:
                    # 自機への方向を計算
                    dx = player_x - self.x
                    dy = player_y - self.y
                    distance = math.sqrt(dx*dx + dy*dy)
                    if distance > 0:
                        # 正規化して速度を掛ける
                        bullet_speed = 3  # 遅い弾速
                        bullet_dx = (dx / distance) * bullet_speed
                        bullet_dy = (dy / distance) * bullet_speed
                        self.bullets.append(TargetBullet(self.x, self.y + self.height // 2, bullet_dx, bullet_dy))
                        self.last_shot = current_time

        elif self.enemy_type == "orange":
            # オレンジの敵：ジグザグ移動
            self.x -= self.speed
            self.y += math.sin(self.time * self.zigzag_frequency) * 2

            # 放射状に弾を撃つ
            current_time = pygame.time.get_ticks()
            if current_time - self.last_shot > self.shot_delay:
                # 8方向に弾を撃つ
                for angle in range(0, 360, 45):
                    bullet_speed = 4
                    dx = bullet_speed * math.cos(math.radians(angle))
                    dy = bullet_speed * math.sin(math.radians(angle))
                    self.bullets.append(TargetBullet(self.x, self.y + self.height // 2, dx, dy))
                self.last_shot = current_time

        # 弾の更新
        self.bullets = [bullet for bullet in self.bullets if bullet.update()]

        return self.x > -self.width

    def draw(self, screen):
        if self.enemy_type == "red":
            # 赤い敵：左向きの三角形
            points = [
                (self.x, self.y + self.height // 2),  # 左の尖った部分
                (self.x + self.width, self.y),        # 右上
                (self.x + self.width, self.y + self.height)  # 右下
            ]
            pygame.draw.polygon(screen, RED, points)

        elif self.enemy_type == "orange":
            # オレンジの敵：六角形
            center_x = self.x + self.width // 2
            center_y = self.y + self.height // 2
            radius = self.width // 2
            points = []
            for i in range(6):
                angle = i * 60  # 60度ずつ
                x = center_x + radius * math.cos(math.radians(angle))
                y = center_y + radius * math.sin(math.radians(angle))
                points.append((x, y))
            pygame.draw.polygon(screen, ORANGE, points)

        # 弾を描画
        for bullet in self.bullets:
            bullet.draw(screen)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

class TargetBullet:
    def __init__(self, x, y, dx, dy):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.width = 6
        self.height = 6

    def update(self):
        self.x += self.dx
        self.y += self.dy
        return (0 <= self.x <= SCREEN_WIDTH and 0 <= self.y <= SCREEN_HEIGHT)

    def draw(self, screen):
        pygame.draw.circle(screen, RED, (int(self.x), int(self.y)), 3)

    def get_rect(self):
        return pygame.Rect(self.x - 3, self.y - 3, self.width, self.height)

class EnemyFormation:
    def __init__(self, x, y, enemy_type="red", count=5):
        self.enemies = []
        if enemy_type == "red":
            # 5体が横に連なって飛んでくる
            for i in range(count):
                enemy_x = x + (i * 40)  # 40ピクセル間隔で左から右に横に配置
                self.enemies.append(Enemy(enemy_x, y, enemy_type, i))
        else:
            # オレンジの敵は単体
            self.enemies.append(Enemy(x, y, enemy_type))

    def update(self, player_x=None, player_y=None):
        self.enemies = [enemy for enemy in self.enemies if enemy.update(player_x, player_y)]
        return len(self.enemies) > 0

    def draw(self, screen):
        for enemy in self.enemies:
            enemy.draw(screen)

    def get_enemies(self):
        return self.enemies

class Boss:
    def __init__(self):
        self.base_x = SCREEN_WIDTH - 150  # より左に配置（サイズが大きくなったため）
        self.x = self.base_x
        self.y = SCREEN_HEIGHT // 2
        self.width = 160  # 2倍に拡大（80 → 160）
        self.height = 240  # 4倍に拡大（60 → 240）
        self.speed = 3
        self.bullets = []
        self.last_shot = 0
        self.shot_delay = 800  # ミリ秒（300から800に頻度を減らす）
        self.health = 30
        self.max_health = 30
        self.time = 0
        self.center_y = SCREEN_HEIGHT // 2
        # レーザー攻撃用
        self.laser_warnings = []  # 予兆
        self.lasers = []
        self.last_laser = 0
        self.laser_delay = 10000  # 10秒間隔
        self.laser_duration = 2000  # 2秒間持続
        self.warning_duration = 1000  # 1秒間の予兆
        self.laser_travel_time = 500  # 0.5秒でレーザーが左端に到達
        self.current_rotation_direction = 1  # 回転方向（1: 時計回り, -1: 反時計回り）

        # ビット（サポートユニット）を4つに増加（左右 + 上下）
        self.bits = [
            BossBit(self, -180, 0),  # 左上のビット（サイズに合わせて拡大）
            BossBit(self, 180, 1),   # 左下のビット（サイズに合わせて拡大）
            BossBit(self, 0, 2, position_type="top"),     # 上のビット（新規追加）
            BossBit(self, 0, 3, position_type="bottom")   # 下のビット（新規追加）
        ]

    def update(self):
        # ゆっくりとした八の字の動き + 前後の動き（上下の振幅を2倍に）
        self.time += 0.03  # 0.05から0.03にさらに減速
        self.y = self.center_y + math.sin(self.time) * 120  # 振幅を2倍に（60 → 120）
        self.x = self.base_x + math.cos(self.time * 0.5) * 20  # 前後の動きはそのまま

        # 通常の弾を撃つ（頻度を減らし、8方向に増やす）
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot > self.shot_delay:
            # 8方向に弾を撃つ
            for angle in range(0, 360, 45):  # 0, 45, 90, 135, 180, 225, 270, 315度の8方向
                bullet_speed = 3
                dx = -bullet_speed * math.cos(math.radians(angle))
                dy = bullet_speed * math.sin(math.radians(angle))
                self.bullets.append(BossBullet(self.x, self.y + self.height // 2, dx, dy))
            self.last_shot = current_time

        # レーザー攻撃システム
        if current_time - self.last_laser > self.laser_delay:
            # 予兆を表示（ボス中心から発射）
            boss_center_x = self.x + self.width // 2
            boss_center_y = self.y + self.height // 2
            laser_angles = [-30, 0, 30]  # 上、中央、下の3方向（角度を広げる）
            # ランダムで時計回りか反時計回りかを決定
            rotation_direction = 1 if random.random() > 0.5 else -1
            for angle in laser_angles:
                self.laser_warnings.append(LaserWarning(boss_center_x, boss_center_y, angle, current_time, self.warning_duration))
            # 回転方向を記録
            self.current_rotation_direction = rotation_direction
            self.last_laser = current_time

        # 弾の更新
        self.bullets = [bullet for bullet in self.bullets if bullet.update()]

        # 予兆の更新と実際のレーザー発射
        active_warnings = []
        for warning in self.laser_warnings:
            if warning.update(current_time):
                active_warnings.append(warning)
            else:
                # 予兆が終了したら実際のレーザーを発射
                self.lasers.append(Laser(warning.start_x, warning.start_y, warning.angle, current_time, self.laser_duration, self.laser_travel_time, self, self.current_rotation_direction))
        self.laser_warnings = active_warnings

        # レーザーの更新
        self.lasers = [laser for laser in self.lasers if laser.update(current_time)]

        # ビットの更新
        for bit in self.bits:
            bit.update()

    def draw(self, screen):
        # 円形大型戦艦として描画（縦4倍サイズ、白縁なし）
        boss_x = int(self.x)
        boss_y = int(self.y)
        center_x = boss_x + self.width // 2
        center_y = boss_y + self.height // 2

        # メインハル（大きな楕円形）- 基本構造（縦長に調整）
        main_radius_x = self.width // 2 - 10
        main_radius_y = self.height // 2 - 10

        # メイン楕円ボディ（灰色ベース）
        main_ellipse = pygame.Rect(center_x - main_radius_x, center_y - main_radius_y,
                                  main_radius_x * 2, main_radius_y * 2)
        pygame.draw.ellipse(screen, (70, 70, 70), main_ellipse)  # ダークグレー

        # 内部構造リング（楕円形の同心円）- 灰色濃淡
        for i in range(4):
            ring_radius_x = main_radius_x - 15 - (i * 10)
            ring_radius_y = main_radius_y - 15 - (i * 10)
            if ring_radius_x > 0 and ring_radius_y > 0:
                ring_color = [(90, 90, 90), (110, 110, 110), (130, 130, 130), (150, 150, 150)][i]  # 灰色グラデーション
                ring_ellipse = pygame.Rect(center_x - ring_radius_x, center_y - ring_radius_y,
                                         ring_radius_x * 2, ring_radius_y * 2)
                pygame.draw.ellipse(screen, ring_color, ring_ellipse, 2)

        # 前方突出部 - ミディアムグレー
        front_extension_points = [
            (center_x + main_radius_x - 10, center_y),
            (center_x + main_radius_x + 30, center_y - 20),
            (center_x + main_radius_x + 40, center_y),
            (center_x + main_radius_x + 30, center_y + 20)
        ]
        pygame.draw.polygon(screen, (100, 100, 100), front_extension_points)

        # 上部セクション（非対称な突出部）- ライトグレー
        upper_section_points = [
            (center_x - 30, center_y - main_radius_y + 20),
            (center_x + 40, center_y - main_radius_y - 10),
            (center_x + 50, center_y - main_radius_y + 30),
            (center_x + 15, center_y - main_radius_y + 50),
            (center_x - 20, center_y - main_radius_y + 40)
        ]
        pygame.draw.polygon(screen, (120, 120, 120), upper_section_points)

        # 下部セクション（非対称な突出部）- ライトグレー
        lower_section_points = [
            (center_x - 35, center_y + main_radius_y - 20),
            (center_x + 35, center_y + main_radius_y + 10),
            (center_x + 45, center_y + main_radius_y - 30),
            (center_x + 10, center_y + main_radius_y - 50),
            (center_x - 25, center_y + main_radius_y - 40)
        ]
        pygame.draw.polygon(screen, (120, 120, 120), lower_section_points)

        # 左側の大型突出部 - ダークグレー
        left_extension_points = [
            (center_x - main_radius_x + 10, center_y - 40),
            (center_x - main_radius_x - 35, center_y - 30),
            (center_x - main_radius_x - 45, center_y),
            (center_x - main_radius_x - 35, center_y + 30),
            (center_x - main_radius_x + 10, center_y + 40)
        ]
        pygame.draw.polygon(screen, (80, 80, 80), left_extension_points)

        # 右側の小型突出部 - ミディアムグレー
        right_extension_points = [
            (center_x + main_radius_x - 10, center_y - 25),
            (center_x + main_radius_x + 20, center_y - 15),
            (center_x + main_radius_x + 30, center_y),
            (center_x + main_radius_x + 20, center_y + 15),
            (center_x + main_radius_x - 10, center_y + 25)
        ]
        pygame.draw.polygon(screen, (110, 110, 110), right_extension_points)

        # 中央コックピット/ブリッジ（楕円形）- 明るいグレー
        bridge_radius_x = 30
        bridge_radius_y = 20
        bridge_ellipse = pygame.Rect(center_x - bridge_radius_x, center_y - bridge_radius_y,
                                   bridge_radius_x * 2, bridge_radius_y * 2)
        pygame.draw.ellipse(screen, (140, 140, 140), bridge_ellipse)

        # ブリッジ窓（複数）
        window_positions = [
            (center_x, center_y - 10),
            (center_x - 15, center_y + 5),
            (center_x + 15, center_y + 5)
        ]
        for wx, wy in window_positions:
            pygame.draw.circle(screen, (200, 220, 255), (wx, wy), 6)

        # 武器システム（複数の砲塔）- 縦長に対応して配置を調整
        weapon_positions = [
            (center_x + 40, center_y - 60),   # 右上
            (center_x + 40, center_y + 60),   # 右下
            (center_x - 40, center_y - 60),   # 左上
            (center_x - 40, center_y + 60),   # 左下
            (center_x, center_y - 80),        # 上
            (center_x, center_y + 80),        # 下
            (center_x + 20, center_y - 100),  # 右上遠
            (center_x - 20, center_y + 100),  # 左下遠
        ]

        for wx, wy in weapon_positions:
            # 砲塔ベース - ダークグレー
            pygame.draw.circle(screen, (60, 60, 60), (wx, wy), 8)
            # 砲身
            pygame.draw.circle(screen, RED, (wx, wy), 4)
            pygame.draw.circle(screen, YELLOW, (wx, wy), 2)

        # メインレーザー発射口（前方突出部に）
        main_laser_x = center_x + main_radius_x + 35
        main_laser_y = center_y
        pygame.draw.circle(screen, RED, (main_laser_x, main_laser_y), 12)
        pygame.draw.circle(screen, YELLOW, (main_laser_x, main_laser_y), 8)
        pygame.draw.circle(screen, WHITE, (main_laser_x, main_laser_y), 4)

        # エンジン（後部に複数）- 縦長に対応して配置を調整
        engine_positions = [
            (center_x - main_radius_x - 25, center_y),        # メインエンジン
            (center_x - main_radius_x + 15, center_y - 40),   # 上部エンジン
            (center_x - main_radius_x + 15, center_y + 40),   # 下部エンジン
            (center_x - main_radius_x - 10, center_y - 20),   # 補助エンジン1
            (center_x - main_radius_x - 10, center_y + 20),   # 補助エンジン2
            (center_x - main_radius_x + 5, center_y - 60),    # 上部補助
            (center_x - main_radius_x + 5, center_y + 60),    # 下部補助
        ]

        engine_sizes = [18, 12, 12, 10, 10, 8, 8]
        for i, (ex, ey) in enumerate(engine_positions):
            size = engine_sizes[i]
            # エンジン炎エフェクト
            pygame.draw.circle(screen, RED, (ex, ey), size)
            pygame.draw.circle(screen, YELLOW, (ex, ey), size - 4)
            pygame.draw.circle(screen, WHITE, (ex, ey), size - 8)

        # 装甲プレート（詳細なライン）- 縦長に対応
        # 放射状のライン
        for angle in range(0, 360, 20):
            start_radius = min(main_radius_x, main_radius_y) - 40
            end_radius = min(main_radius_x, main_radius_y) - 20
            start_x = center_x + start_radius * math.cos(math.radians(angle))
            start_y = center_y + start_radius * math.sin(math.radians(angle))
            end_x = center_x + end_radius * math.cos(math.radians(angle))
            end_y = center_y + end_radius * math.sin(math.radians(angle))
            pygame.draw.line(screen, (120, 120, 120), (start_x, start_y), (end_x, end_y), 1)

        # 格子状の装甲ライン - 灰色
        for i in range(-3, 4):
            # 縦線
            line_x = center_x + i * 25
            pygame.draw.line(screen, (100, 100, 100),
                           (line_x, center_y - main_radius_y + 30),
                           (line_x, center_y + main_radius_y - 30), 1)

        for i in range(-6, 7):
            # 横線（縦長に対応して増加）
            line_y = center_y + i * 20
            pygame.draw.line(screen, (100, 100, 100),
                           (center_x - main_radius_x + 30, line_y),
                           (center_x + main_radius_x - 30, line_y), 1)

        # 通信アンテナ/センサー（小さな突起）- 灰色
        antenna_positions = [
            (center_x + 20, center_y - 70),
            (center_x - 25, center_y - 80),
            (center_x + 30, center_y + 40),
            (center_x - 20, center_y + 70),
            (center_x, center_y - 100),
            (center_x, center_y + 100)
        ]

        for ax, ay in antenna_positions:
            pygame.draw.circle(screen, (130, 130, 130), (ax, ay), 3)
            # アンテナの線
            pygame.draw.line(screen, (110, 110, 110), (ax, ay), (ax + 5, ay - 8), 1)

        # 体力バーを描画
        bar_width = 200
        bar_height = 20
        bar_x = SCREEN_WIDTH - bar_width - 10
        bar_y = 10

        # 背景
        pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_width, bar_height))
        # 現在の体力
        current_width = int((self.health / self.max_health) * bar_width)
        pygame.draw.rect(screen, GREEN, (bar_x, bar_y, current_width, bar_height))
        # 枠
        pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)

        # ボス名表示
        boss_name_text = game_font.render("BOSS: Millennium Destroyer", True, WHITE)
        screen.blit(boss_name_text, (bar_x, bar_y - 25))

        # 弾を描画
        for bullet in self.bullets:
            bullet.draw(screen)

        # 予兆を描画
        for warning in self.laser_warnings:
            warning.draw(screen)

        # レーザーを描画
        for laser in self.lasers:
            laser.draw(screen)

        # ビットを描画
        for bit in self.bits:
            bit.draw(screen)

    def get_rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def get_lasers(self):
        return self.lasers

    def get_bits(self):
        return self.bits

class LaserWarning:
    def __init__(self, start_x, start_y, angle, start_time, duration):
        self.start_x = start_x
        self.start_y = start_y
        self.angle = angle
        self.start_time = start_time
        self.duration = duration

        # 予兆の終点を計算（画面左端まで）
        self.end_x = 0
        self.end_y = start_y + (start_x * math.tan(math.radians(angle)))

    def update(self, current_time):
        # 持続時間をチェック
        return current_time - self.start_time < self.duration

    def draw(self, screen):
        # 薄い赤色で予兆を描画（点滅効果を追加）
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.start_time

        # 点滅効果（0.2秒間隔）
        if (elapsed // 200) % 2 == 0:
            light_red = (100, 50, 50)
            pygame.draw.line(screen, light_red, (self.start_x, self.start_y), (self.end_x, self.end_y), 4)

class Laser:
    def __init__(self, start_x, start_y, angle, start_time, duration, travel_time, boss_ref, rotation_direction):
        self.initial_start_x = start_x
        self.initial_start_y = start_y
        self.initial_angle = angle
        self.start_time = start_time
        self.duration = duration
        self.travel_time = travel_time
        self.width = 24  # レーザーをさらに太くする（12から24に、2倍）
        self.boss_ref = boss_ref  # ボスへの参照
        self.rotation_direction = rotation_direction  # 回転方向
        self.rotation_speed = 7.5  # 2秒で15度回転（7.5度/秒）

        # ボスからの相対位置を記録（中心からの発射に修正）
        self.offset_x = 0  # ボス中心からの相対位置なので0
        self.offset_y = 0  # ボス中心からの相対位置なので0

    def update(self, current_time):
        # 持続時間をチェック
        return current_time - self.start_time < self.duration

    def get_current_angle(self, current_time):
        # 経過時間に基づいて角度を計算
        elapsed = current_time - self.start_time
        rotation_amount = (elapsed / 1000.0) * self.rotation_speed * self.rotation_direction
        return self.initial_angle + rotation_amount

    def get_current_start_position(self):
        # ボスの現在の中心位置からレーザーを発射
        current_start_x = self.boss_ref.x + self.boss_ref.width // 2
        current_start_y = self.boss_ref.y + self.boss_ref.height // 2
        return current_start_x, current_start_y

    def get_current_end_position(self, current_time):
        current_start_x, current_start_y = self.get_current_start_position()
        current_angle = self.get_current_angle(current_time)

        # レーザーが徐々に左端まで伸びる
        elapsed = current_time - self.start_time
        if elapsed >= self.travel_time:
            # 完全に伸びた状態
            laser_length = 1500  # 十分に長い距離
            final_end_x = current_start_x - laser_length * math.cos(math.radians(current_angle))
            final_end_y = current_start_y - laser_length * math.sin(math.radians(current_angle))
            return final_end_x, final_end_y

        # 進行度を計算
        progress = elapsed / self.travel_time
        laser_length = 1500 * progress
        current_end_x = current_start_x - laser_length * math.cos(math.radians(current_angle))
        current_end_y = current_start_y - laser_length * math.sin(math.radians(current_angle))
        return current_end_x, current_end_y

    def draw(self, screen):
        current_time = pygame.time.get_ticks()
        start_x, start_y = self.get_current_start_position()
        end_x, end_y = self.get_current_end_position(current_time)

        # レーザーを赤い線で描画（さらに太く）
        pygame.draw.line(screen, RED, (int(start_x), int(start_y)), (int(end_x), int(end_y)), self.width)

        # レーザーの光る効果（中心に白い線）
        pygame.draw.line(screen, WHITE, (int(start_x), int(start_y)), (int(end_x), int(end_y)), 8)

    def get_collision_rect(self):
        current_time = pygame.time.get_ticks()
        start_x, start_y = self.get_current_start_position()
        end_x, end_y = self.get_current_end_position(current_time)

        # レーザーの当たり判定用の矩形を返す
        min_x = min(start_x, end_x)
        max_x = max(start_x, end_x)
        min_y = min(start_y, end_y) - self.width // 2
        max_y = max(start_y, end_y) + self.width // 2
        return pygame.Rect(min_x, min_y, max_x - min_x, max_y - min_y)

class BossBit:
    def __init__(self, boss_ref, position_offset_y, bit_id, position_type="side"):
        self.boss_ref = boss_ref
        self.position_offset_y = position_offset_y  # ボスからの相対Y位置
        self.bit_id = bit_id
        self.position_type = position_type  # "side", "top", "bottom"
        self.width = 35  # ビットを大きくする（20から35に）
        self.height = 25  # ビットを大きくする（15から25に）
        self.bullets = []
        self.last_shot = 0
        self.shot_delay = 1500  # 弾数を増やす（2.5秒から1.5秒に短縮）
        self.float_time = 0
        self.float_amplitude = 20  # 浮遊の振幅を大きく
        self.float_speed = 0.03

    def update(self):
        self.float_time += self.float_speed

        # ビットから弾を撃つ（弾数を増やす）
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot > self.shot_delay:
            bit_x, bit_y = self.get_position()
            # 複数方向に弾を撃つ（速度を遅く）
            for angle in [-10, 0, 10]:  # 3方向に弾を撃つ
                dx = -1.5 * math.cos(math.radians(angle))  # 速度を半分に（-3 → -1.5）
                dy = -1.5 * math.sin(math.radians(angle))  # 速度を半分に（-3 → -1.5）
                self.bullets.append(BossBullet(bit_x, bit_y, dx, dy))
            self.last_shot = current_time

        # 弾の更新
        self.bullets = [bullet for bullet in self.bullets if bullet.update()]

    def get_position(self):
        # ボスの位置に基づいてビットの位置を計算
        if self.position_type == "side":
            # 左右のビット（従来通り）
            base_x = self.boss_ref.x - 100  # ボスからさらに離す
            base_y = self.boss_ref.y + self.boss_ref.height // 2 + self.position_offset_y
        elif self.position_type == "top":
            # 上のビット
            base_x = self.boss_ref.x + self.boss_ref.width // 2
            base_y = self.boss_ref.y - 150  # ボスからかなり離す
        elif self.position_type == "bottom":
            # 下のビット
            base_x = self.boss_ref.x + self.boss_ref.width // 2
            base_y = self.boss_ref.y + self.boss_ref.height + 150  # ボスからかなり離す

        # 浮遊効果を追加
        float_offset = math.sin(self.float_time + self.bit_id) * self.float_amplitude

        if self.position_type == "side":
            return base_x, base_y + float_offset
        else:  # top or bottom
            return base_x + float_offset, base_y

    def draw(self, screen):
        bit_x, bit_y = self.get_position()

        # ビットのメインボディ（大きな八角形）
        center_x = bit_x + self.width // 2
        center_y = bit_y + self.height // 2
        radius = 12  # 半径を大きく
        points = []
        for i in range(8):  # 8角形に変更
            angle = i * 45
            x = center_x + radius * math.cos(math.radians(angle))
            y = center_y + radius * math.sin(math.radians(angle))
            points.append((x, y))
        pygame.draw.polygon(screen, (200, 0, 200), points)
        pygame.draw.polygon(screen, WHITE, points, 2)

        # ビットの中央コア（大きく）
        pygame.draw.circle(screen, RED, (int(center_x), int(center_y)), 5)
        pygame.draw.circle(screen, YELLOW, (int(center_x), int(center_y)), 3)
        pygame.draw.circle(screen, WHITE, (int(center_x), int(center_y)), 1)

        # 装飾リング
        pygame.draw.circle(screen, (150, 0, 150), (int(center_x), int(center_y)), 8, 1)

        # エネルギーライン（ボスとの接続線）
        boss_center_x = self.boss_ref.x + self.boss_ref.width // 2
        boss_center_y = self.boss_ref.y + self.boss_ref.height // 2

        # 薄い紫色の接続線（太く）
        pygame.draw.line(screen, (100, 0, 100), (int(center_x), int(center_y)),
                        (int(boss_center_x), int(boss_center_y)), 2)

        # 弾を描画
        for bullet in self.bullets:
            bullet.draw(screen)

    def get_rect(self):
        bit_x, bit_y = self.get_position()
        return pygame.Rect(bit_x, bit_y, self.width, self.height)

    def get_bullets(self):
        return self.bullets

class BossBullet:
    def __init__(self, x, y, dx, dy):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.width = 10  # サイズを大きく（6 → 10）
        self.height = 10  # サイズを大きく（6 → 10）
        self.radius = 5  # 描画用の半径も大きく（3 → 5）

    def update(self):
        self.x += self.dx
        self.y += self.dy
        return (0 <= self.x <= SCREEN_WIDTH and 0 <= self.y <= SCREEN_HEIGHT)

    def draw(self, screen):
        # ビットの弾を青緑色で大きく描画
        pygame.draw.circle(screen, (0, 255, 200), (int(self.x), int(self.y)), self.radius)  # シアン系
        pygame.draw.circle(screen, (100, 255, 255), (int(self.x), int(self.y)), self.radius - 2)  # 明るいシアン
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.radius - 4)  # 中心の白

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.width, self.height)

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False

    def draw(self, screen):
        # ボタンの色を決定
        current_color = self.hover_color if self.is_hovered else self.color

        # ボタンを描画
        pygame.draw.rect(screen, current_color, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 3)

        # テキストを描画
        text_surface = button_font.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return True
        return False

def show_game_clear_screen():
    """ゲームクリア画面を表示（タイトル画面と同じテイスト）"""
    clock = pygame.time.Clock()
    time_counter = 0

    # 統一カラーパレット（青紫系 + 勝利の金色）
    CLEAR_MAIN = (255, 215, 0)        # ゴールド（メイン）
    CLEAR_ACCENT = (255, 165, 0)      # オレンジゴールド（アクセント）
    CLEAR_BLUE = (100, 150, 255)      # タイトルと同じブルー
    CLEAR_PURPLE = (150, 100, 255)    # タイトルと同じ紫
    CLEAR_GLOW = (255, 255, 150)      # 明るいゴールドグロー
    CLEAR_DARK = (100, 80, 0)         # ダークゴールド
    CLEAR_BRIGHT = (255, 255, 200)    # ブライトゴールド

    # 星の背景用（勝利エフェクト付き）
    stars = []
    victory_particles = []

    # 通常の星
    for _ in range(100):
        stars.append({
            'x': random.randint(0, SCREEN_WIDTH),
            'y': random.randint(0, SCREEN_HEIGHT),
            'speed': random.uniform(0.3, 1.5),
            'brightness': random.randint(80, 200),
            'color_type': random.choice(['blue', 'purple', 'gold'])
        })

    # 勝利パーティクル
    for _ in range(50):
        victory_particles.append({
            'x': random.randint(0, SCREEN_WIDTH),
            'y': random.randint(0, SCREEN_HEIGHT),
            'speed_x': random.uniform(-2, 2),
            'speed_y': random.uniform(-3, 1),
            'size': random.randint(2, 6),
            'color_type': random.choice(['gold', 'orange', 'yellow']),
            'life': random.randint(60, 180),
            'max_life': 180
        })

    while True:
        time_counter += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # キーボード操作
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  # Rキーでリスタート
                    return "restart"
                elif event.key == pygame.K_ESCAPE:  # ESCキーでタイトルに戻る
                    return "title"

        # 画面をダークブルーのグラデーションで塗りつぶし（タイトルと同じ）
        for y in range(SCREEN_HEIGHT):
            color_ratio = y / SCREEN_HEIGHT
            r = int(10 + color_ratio * 20)
            g = int(20 + color_ratio * 30)
            b = int(40 + color_ratio * 60)
            pygame.draw.line(screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

        # 動く星の背景（勝利カラー追加）
        for star in stars:
            star['x'] -= star['speed']
            if star['x'] < 0:
                star['x'] = SCREEN_WIDTH
                star['y'] = random.randint(0, SCREEN_HEIGHT)

            brightness = star['brightness']
            if star['color_type'] == 'blue':
                color = (brightness//3, brightness//2, brightness)
            elif star['color_type'] == 'purple':
                color = (brightness//2, brightness//3, brightness)
            else:  # gold
                color = (brightness, brightness//2, brightness//4)

            pygame.draw.circle(screen, color, (int(star['x']), int(star['y'])), 1)

        # 勝利パーティクルの更新と描画
        for particle in victory_particles[:]:
            particle['x'] += particle['speed_x']
            particle['y'] += particle['speed_y']
            particle['life'] -= 1

            # 画面外に出たら再生成
            if (particle['x'] < 0 or particle['x'] > SCREEN_WIDTH or
                particle['y'] < 0 or particle['y'] > SCREEN_HEIGHT or
                particle['life'] <= 0):
                particle['x'] = random.randint(0, SCREEN_WIDTH)
                particle['y'] = SCREEN_HEIGHT + random.randint(10, 50)
                particle['speed_x'] = random.uniform(-2, 2)
                particle['speed_y'] = random.uniform(-3, 1)
                particle['life'] = particle['max_life']

            # パーティクルの色と透明度
            life_ratio = particle['life'] / particle['max_life']
            if particle['color_type'] == 'gold':
                color = (int(255 * life_ratio), int(215 * life_ratio), 0)
            elif particle['color_type'] == 'orange':
                color = (int(255 * life_ratio), int(165 * life_ratio), 0)
            else:  # yellow
                color = (int(255 * life_ratio), int(255 * life_ratio), int(100 * life_ratio))

            pygame.draw.circle(screen, color, (int(particle['x']), int(particle['y'])), particle['size'])

        # メインタイトルの背景エフェクト（勝利グロー）
        title_glow_size = 12 + int(math.sin(time_counter * 0.1) * 6)
        for i in range(title_glow_size):
            alpha = 80 - (i * 5)
            if alpha > 0:
                glow_color = CLEAR_GLOW
                title_text_glow = title_font.render("MISSION COMPLETE", True, glow_color)
                glow_rect = title_text_glow.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 200))
                screen.blit(title_text_glow, (glow_rect.x - i*2, glow_rect.y - i))

        # メインタイトル（勝利メッセージ）
        title_text = title_font.render("MISSION COMPLETE", True, CLEAR_BRIGHT)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 200))
        screen.blit(title_text, title_rect)

        # タイトル装飾（ゴールドアクセント）
        title_decoration = title_font.render("MISSION COMPLETE", True, CLEAR_MAIN)
        screen.blit(title_decoration, (title_rect.x + 4, title_rect.y + 4))

        # サブタイトル（勝利メッセージ）
        subtitle_text = button_font.render("- GALACTIC PEACE RESTORED -", True, CLEAR_ACCENT)
        subtitle_rect = subtitle_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 150))
        screen.blit(subtitle_text, subtitle_rect)

        # 勝利メッセージ
        victory_msg = game_font.render("The galaxy is safe once again, brave pilot!", True, CLEAR_BLUE)
        victory_rect = victory_msg.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 100))
        screen.blit(victory_msg, victory_rect)

        # 装飾的な勝利宇宙船（中央・大きく）
        ship_scale = 1.5 + math.sin(time_counter * 0.05) * 0.3
        ship_x = SCREEN_WIDTH//2
        ship_y = SCREEN_HEIGHT//2 - 20

        # 勝利宇宙船（プレイヤー機をベースに拡大・装飾）
        ship_size = int(40 * ship_scale)
        ship_height = int(30 * ship_scale)
        ship_points = [
            (ship_x + ship_size, ship_y),
            (ship_x - ship_size//2, ship_y - ship_height//2),
            (ship_x - ship_size//2, ship_y + ship_height//2)
        ]
        pygame.draw.polygon(screen, CLEAR_MAIN, ship_points)
        pygame.draw.polygon(screen, CLEAR_BRIGHT, ship_points, 4)

        # 勝利エンジンエフェクト（豪華に）
        engine_length = int(60 * ship_scale)
        for i in range(5):
            engine_color = [CLEAR_MAIN, CLEAR_ACCENT, YELLOW, WHITE, CLEAR_GLOW][i]
            engine_width = 8 - i
            if engine_width > 0:
                pygame.draw.line(screen, engine_color,
                               (ship_x - ship_size//2, ship_y),
                               (ship_x - ship_size//2 - engine_length + i*8, ship_y),
                               engine_width)

        # 勝利の光輪
        halo_radius = int(80 + math.sin(time_counter * 0.08) * 20)
        for i in range(3):
            halo_color = [CLEAR_GLOW, CLEAR_MAIN, CLEAR_ACCENT][i]
            pygame.draw.circle(screen, halo_color, (ship_x, ship_y), halo_radius - i*15, 2)

        # 左右の護衛機（小さく）
        escort_offset = 150
        escort_y_offset = int(math.sin(time_counter * 0.06) * 30)

        # 左の護衛機
        left_escort_x = ship_x - escort_offset
        left_escort_y = ship_y + 50 + escort_y_offset
        left_points = [
            (left_escort_x + 25, left_escort_y),
            (left_escort_x - 10, left_escort_y - 12),
            (left_escort_x - 10, left_escort_y + 12)
        ]
        pygame.draw.polygon(screen, CLEAR_BLUE, left_points)
        pygame.draw.polygon(screen, CLEAR_BRIGHT, left_points, 2)

        # 右の護衛機
        right_escort_x = ship_x + escort_offset
        right_escort_y = ship_y + 50 - escort_y_offset
        right_points = [
            (right_escort_x + 25, right_escort_y),
            (right_escort_x - 10, right_escort_y - 12),
            (right_escort_x - 10, right_escort_y + 12)
        ]
        pygame.draw.polygon(screen, CLEAR_PURPLE, right_points)
        pygame.draw.polygon(screen, CLEAR_BRIGHT, right_points, 2)

        # 操作説明（タイトルと同じスタイル）
        key_help_text = button_font.render("Press R to Restart, ESC to Title", True, CLEAR_MAIN)
        key_help_rect = key_help_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 150))
        screen.blit(key_help_text, key_help_rect)

        # 詳細操作説明
        detail_help = game_font.render("Thank you for playing Spaceship Shooting!", True, CLEAR_BLUE)
        detail_rect = detail_help.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 200))
        screen.blit(detail_help, detail_rect)

        # 装飾的な境界線（勝利カラー・グラデーション）
        for i in range(5):
            alpha = 120 - i * 20
            line_color = CLEAR_MAIN if i % 2 == 0 else CLEAR_ACCENT
            pygame.draw.line(screen, line_color, (50, SCREEN_HEIGHT//2 - 250 + i), (SCREEN_WIDTH - 50, SCREEN_HEIGHT//2 - 250 + i), 3)
            pygame.draw.line(screen, line_color, (50, SCREEN_HEIGHT//2 + 250 + i), (SCREEN_WIDTH - 50, SCREEN_HEIGHT//2 + 250 + i), 3)

        # 角の装飾（勝利カラー・より豪華）
        corner_size = 50
        corner_color = CLEAR_BRIGHT
        # 左上
        pygame.draw.lines(screen, corner_color, False, [(50, 50), (50, 50 + corner_size), (50 + corner_size, 50)], 4)
        pygame.draw.lines(screen, CLEAR_MAIN, False, [(55, 55), (55, 55 + corner_size - 15), (55 + corner_size - 15, 55)], 3)

        # 右上
        pygame.draw.lines(screen, corner_color, False, [(SCREEN_WIDTH - 50, 50), (SCREEN_WIDTH - 50, 50 + corner_size), (SCREEN_WIDTH - 50 - corner_size, 50)], 4)
        pygame.draw.lines(screen, CLEAR_MAIN, False, [(SCREEN_WIDTH - 55, 55), (SCREEN_WIDTH - 55, 55 + corner_size - 15), (SCREEN_WIDTH - 55 - corner_size + 15, 55)], 3)

        # 左下
        pygame.draw.lines(screen, corner_color, False, [(50, SCREEN_HEIGHT - 50), (50, SCREEN_HEIGHT - 50 - corner_size), (50 + corner_size, SCREEN_HEIGHT - 50)], 4)
        pygame.draw.lines(screen, CLEAR_MAIN, False, [(55, SCREEN_HEIGHT - 55), (55, SCREEN_HEIGHT - 55 - corner_size + 15), (55 + corner_size - 15, SCREEN_HEIGHT - 55)], 3)

        # 右下
        pygame.draw.lines(screen, corner_color, False, [(SCREEN_WIDTH - 50, SCREEN_HEIGHT - 50), (SCREEN_WIDTH - 50, SCREEN_HEIGHT - 50 - corner_size), (SCREEN_WIDTH - 50 - corner_size, SCREEN_HEIGHT - 50)], 4)
        pygame.draw.lines(screen, CLEAR_MAIN, False, [(SCREEN_WIDTH - 55, SCREEN_HEIGHT - 55), (SCREEN_WIDTH - 55, SCREEN_HEIGHT - 55 - corner_size + 15), (SCREEN_WIDTH - 55 - corner_size + 15, SCREEN_HEIGHT - 55)], 3)

        # 中央装飾エフェクト（勝利の輝き）
        center_pulse = 50 + int(math.sin(time_counter * 0.12) * 15)
        pygame.draw.circle(screen, CLEAR_GLOW, (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50), center_pulse, 3)
        pygame.draw.circle(screen, CLEAR_MAIN, (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50), center_pulse - 15, 2)

        # 画面を更新
        pygame.display.flip()
        clock.tick(60)

def show_title_screen():
    """タイトル画面を表示"""
    clock = pygame.time.Clock()
    time_counter = 0

    # 統一カラーパレット（青紫系）
    TITLE_MAIN = (100, 150, 255)      # メインブルー
    TITLE_ACCENT = (150, 100, 255)    # アクセント紫
    TITLE_GLOW = (50, 100, 200)       # グロー効果
    TITLE_DARK = (30, 50, 100)        # ダークブルー
    TITLE_BRIGHT = (200, 220, 255)    # ブライトブルー

    # ボタンを作成（統一カラー）
    start_button = Button(SCREEN_WIDTH//2 - 120, SCREEN_HEIGHT//2 + 50, 240, 70, "Start", TITLE_DARK, TITLE_MAIN)
    end_button = Button(SCREEN_WIDTH//2 - 120, SCREEN_HEIGHT//2 + 150, 240, 70, "End", TITLE_DARK, TITLE_ACCENT)

    # 星の背景用
    stars = []
    for _ in range(150):
        stars.append({
            'x': random.randint(0, SCREEN_WIDTH),
            'y': random.randint(0, SCREEN_HEIGHT),
            'speed': random.uniform(0.3, 1.5),
            'brightness': random.randint(80, 200),
            'color_type': random.choice(['blue', 'purple', 'white'])
        })

    while True:
        time_counter += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # キーボード操作を追加
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s:  # Sキーでスタート
                    return "start"
                elif event.key == pygame.K_e:  # Eキーで終了
                    return "end"

            # ボタンのイベント処理
            if start_button.handle_event(event):
                return "start"
            if end_button.handle_event(event):
                return "end"

        # 画面をダークブルーのグラデーションで塗りつぶし
        for y in range(SCREEN_HEIGHT):
            color_ratio = y / SCREEN_HEIGHT
            r = int(10 + color_ratio * 20)
            g = int(20 + color_ratio * 30)
            b = int(40 + color_ratio * 60)
            pygame.draw.line(screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

        # 動く星の背景（統一カラー）
        for star in stars:
            star['x'] -= star['speed']
            if star['x'] < 0:
                star['x'] = SCREEN_WIDTH
                star['y'] = random.randint(0, SCREEN_HEIGHT)

            brightness = star['brightness']
            if star['color_type'] == 'blue':
                color = (brightness//3, brightness//2, brightness)
            elif star['color_type'] == 'purple':
                color = (brightness//2, brightness//3, brightness)
            else:
                color = (brightness, brightness, brightness)

            pygame.draw.circle(screen, color, (int(star['x']), int(star['y'])), 1)

        # タイトルロゴの背景エフェクト（統一カラー）
        title_glow_size = 8 + int(math.sin(time_counter * 0.08) * 4)
        for i in range(title_glow_size):
            alpha = 60 - (i * 6)
            if alpha > 0:
                glow_color = (*TITLE_GLOW, alpha)
                title_text_glow = title_font.render("Spaceship Shooting", True, glow_color)
                glow_rect = title_text_glow.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 150))
                screen.blit(title_text_glow, (glow_rect.x - i*2, glow_rect.y - i))

        # メインタイトル（統一カラー）
        title_text = title_font.render("Spaceship Shooting", True, TITLE_BRIGHT)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 150))
        screen.blit(title_text, title_rect)

        # タイトル装飾（アクセントカラー）
        title_decoration = title_font.render("Spaceship Shooting", True, TITLE_ACCENT)
        screen.blit(title_decoration, (title_rect.x + 3, title_rect.y + 3))

        # サブタイトル（統一カラー）
        subtitle_text = button_font.render("- Galactic War -", True, TITLE_MAIN)
        subtitle_rect = subtitle_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 100))
        screen.blit(subtitle_text, subtitle_rect)

        # 装飾的な宇宙船（左側・統一カラー）
        ship_x = 100 + int(math.sin(time_counter * 0.04) * 25)
        ship_y = SCREEN_HEIGHT//2 - 50
        ship_points = [
            (ship_x + 50, ship_y),
            (ship_x, ship_y - 20),
            (ship_x, ship_y + 20)
        ]
        pygame.draw.polygon(screen, TITLE_MAIN, ship_points)
        pygame.draw.polygon(screen, TITLE_BRIGHT, ship_points, 3)

        # エンジンエフェクト（統一カラー）
        engine_length = 20 + int(math.sin(time_counter * 0.25) * 8)
        pygame.draw.line(screen, TITLE_ACCENT, (ship_x, ship_y), (ship_x - engine_length, ship_y), 4)
        pygame.draw.line(screen, TITLE_BRIGHT, (ship_x, ship_y), (ship_x - engine_length + 8, ship_y), 2)

        # 装飾的な宇宙船（右側・統一カラー）
        ship2_x = SCREEN_WIDTH - 100 + int(math.sin(time_counter * 0.06) * 20)
        ship2_y = SCREEN_HEIGHT//2 + 50
        ship2_points = [
            (ship2_x - 50, ship2_y),
            (ship2_x, ship2_y - 18),
            (ship2_x, ship2_y + 18)
        ]
        pygame.draw.polygon(screen, TITLE_ACCENT, ship2_points)
        pygame.draw.polygon(screen, TITLE_BRIGHT, ship2_points, 3)

        # エンジンエフェクト2（統一カラー）
        engine2_length = 18 + int(math.sin(time_counter * 0.35) * 6)
        pygame.draw.line(screen, TITLE_MAIN, (ship2_x, ship2_y), (ship2_x + engine2_length, ship2_y), 4)
        pygame.draw.line(screen, TITLE_BRIGHT, (ship2_x, ship2_y), (ship2_x + engine2_length - 6, ship2_y), 2)

        # ボタンを描画
        start_button.draw(screen)
        end_button.draw(screen)

        # キーボード操作の説明（統一カラー）
        key_help_text = game_font.render("Press S to Start, E to End, or click buttons", True, TITLE_MAIN)
        key_help_rect = key_help_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 250))
        screen.blit(key_help_text, key_help_rect)

        # 装飾的な境界線（統一カラー・グラデーション）
        for i in range(5):
            alpha = 100 - i * 15
            line_color = (*TITLE_ACCENT, alpha) if i % 2 == 0 else (*TITLE_MAIN, alpha)
            pygame.draw.line(screen, line_color[:3], (50, SCREEN_HEIGHT//2 - 200 + i), (SCREEN_WIDTH - 50, SCREEN_HEIGHT//2 - 200 + i), 2)
            pygame.draw.line(screen, line_color[:3], (50, SCREEN_HEIGHT//2 + 300 + i), (SCREEN_WIDTH - 50, SCREEN_HEIGHT//2 + 300 + i), 2)

        # 角の装飾（統一カラー・より複雑）
        corner_size = 40
        corner_color = TITLE_BRIGHT
        # 左上
        pygame.draw.lines(screen, corner_color, False, [(50, 50), (50, 50 + corner_size), (50 + corner_size, 50)], 3)
        pygame.draw.lines(screen, TITLE_MAIN, False, [(55, 55), (55, 55 + corner_size - 10), (55 + corner_size - 10, 55)], 2)

        # 右上
        pygame.draw.lines(screen, corner_color, False, [(SCREEN_WIDTH - 50, 50), (SCREEN_WIDTH - 50, 50 + corner_size), (SCREEN_WIDTH - 50 - corner_size, 50)], 3)
        pygame.draw.lines(screen, TITLE_MAIN, False, [(SCREEN_WIDTH - 55, 55), (SCREEN_WIDTH - 55, 55 + corner_size - 10), (SCREEN_WIDTH - 55 - corner_size + 10, 55)], 2)

        # 左下
        pygame.draw.lines(screen, corner_color, False, [(50, SCREEN_HEIGHT - 50), (50, SCREEN_HEIGHT - 50 - corner_size), (50 + corner_size, SCREEN_HEIGHT - 50)], 3)
        pygame.draw.lines(screen, TITLE_MAIN, False, [(55, SCREEN_HEIGHT - 55), (55, SCREEN_HEIGHT - 55 - corner_size + 10), (55 + corner_size - 10, SCREEN_HEIGHT - 55)], 2)

        # 右下
        pygame.draw.lines(screen, corner_color, False, [(SCREEN_WIDTH - 50, SCREEN_HEIGHT - 50), (SCREEN_WIDTH - 50, SCREEN_HEIGHT - 50 - corner_size), (SCREEN_WIDTH - 50 - corner_size, SCREEN_HEIGHT - 50)], 3)
        pygame.draw.lines(screen, TITLE_MAIN, False, [(SCREEN_WIDTH - 55, SCREEN_HEIGHT - 55), (SCREEN_WIDTH - 55, SCREEN_HEIGHT - 55 - corner_size + 10), (SCREEN_WIDTH - 55 - corner_size + 10, SCREEN_HEIGHT - 55)], 2)

        # 中央装飾エフェクト
        center_pulse = 30 + int(math.sin(time_counter * 0.1) * 10)
        pygame.draw.circle(screen, (*TITLE_GLOW, 30), (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50), center_pulse, 2)
        pygame.draw.circle(screen, (*TITLE_MAIN, 50), (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50), center_pulse - 10, 1)

        # 画面を更新
        pygame.display.flip()
        clock.tick(60)

def run_game():
    """ゲーム本体"""
    clock = pygame.time.Clock()

    # ゲームオブジェクトの初期化
    player = Player()
    enemy_formations = []
    boss = None
    enemy_spawn_timer = 0
    enemy_spawn_delay = 3000  # 3秒間隔
    enemy_count = 0
    boss_spawned = False
    game_state = "playing"  # "playing", "game_over", "game_clear"

    while True:
        current_time = pygame.time.get_ticks()
        keys_pressed = pygame.key.get_pressed()
        shift_key_event = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return
                if event.key == pygame.K_r and game_state != "playing":
                    # ゲームリスタート
                    return run_game()
                if event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                    shift_key_event = True

        if game_state == "playing":
            # プレイヤーの更新
            player.update(keys_pressed, shift_key_event)

            # 敵のスポーン
            if not boss_spawned and current_time - enemy_spawn_timer > enemy_spawn_delay:
                spawn_y = random.randint(100, SCREEN_HEIGHT - 100)  # 横並びなので通常の範囲

                # ランダムで敵の種類を決定
                if random.random() < 0.7:  # 70%の確率で赤い敵の編隊
                    enemy_formations.append(EnemyFormation(SCREEN_WIDTH, spawn_y, "red", 5))
                else:  # 30%の確率でオレンジの敵
                    enemy_formations.append(EnemyFormation(SCREEN_WIDTH, spawn_y, "orange", 1))

                enemy_spawn_timer = current_time

            # 敵編隊の更新
            player_center_x = player.x + player.width // 2
            player_center_y = player.y + player.height // 2
            enemy_formations = [formation for formation in enemy_formations
                              if formation.update(player_center_x, player_center_y)]

            # ボスのスポーン
            if enemy_count >= 30 and not boss_spawned:
                boss = Boss()
                boss_spawned = True
                enemy_formations.clear()  # 通常の敵を全て削除

            # ボスの更新
            if boss:
                boss.update()

            # 衝突判定
            player_rect = player.get_rect()

            # プレイヤーと敵の衝突（無敵状態でなければ）
            if not player.is_invincible():
                for formation in enemy_formations:
                    for enemy in formation.get_enemies():
                        if player_rect.colliderect(enemy.get_rect()):
                            game_state = "game_over"
                            break

                        # プレイヤーと敵の弾の衝突
                        for bullet in enemy.bullets:
                            if player_rect.colliderect(bullet.get_rect()):
                                game_state = "game_over"
                                break
                    if game_state == "game_over":
                        break

            # プレイヤーとボスの衝突（無敵状態でなければ）
            if boss and not player.is_invincible() and player_rect.colliderect(boss.get_rect()):
                game_state = "game_over"

            # プレイヤーとボスの弾・レーザー・ビットの衝突（無敵状態でなければ）
            if boss and not player.is_invincible():
                for bullet in boss.bullets:
                    if player_rect.colliderect(bullet.get_rect()):
                        game_state = "game_over"
                        break

                # プレイヤーとボスのレーザーの衝突
                for laser in boss.get_lasers():
                    if player_rect.colliderect(laser.get_collision_rect()):
                        game_state = "game_over"
                        break

                # プレイヤーとビットの衝突
                for bit in boss.get_bits():
                    if player_rect.colliderect(bit.get_rect()):
                        game_state = "game_over"
                        break

                    # プレイヤーとビットの弾の衝突
                    for bullet in bit.get_bullets():
                        if player_rect.colliderect(bullet.get_rect()):
                            game_state = "game_over"
                            break

            # プレイヤーの弾と敵の衝突
            for bullet in player.bullets[:]:
                hit = False
                for formation in enemy_formations[:]:
                    for enemy in formation.get_enemies()[:]:
                        if bullet.get_rect().colliderect(enemy.get_rect()):
                            player.bullets.remove(bullet)
                            formation.enemies.remove(enemy)
                            enemy_count += 1
                            hit = True
                            break
                    if hit:
                        break
                if hit:
                    continue

            # プレイヤーの弾とボス・ビットの衝突
            if boss:
                for bullet in player.bullets[:]:
                    # ボス本体との衝突
                    if bullet.get_rect().colliderect(boss.get_rect()):
                        player.bullets.remove(bullet)
                        boss.health -= 1
                        if boss.health <= 0:
                            game_state = "game_clear"
                        break

                    # ビットとの衝突
                    hit_bit = False
                    for bit in boss.get_bits():
                        if bullet.get_rect().colliderect(bit.get_rect()):
                            player.bullets.remove(bullet)
                            # ビットは破壊されない（装甲が厚い設定）
                            hit_bit = True
                            break
                    if hit_bit:
                        continue

        # 画面を黒で塗りつぶし
        screen.fill(BLACK)

        if game_state == "playing":
            # ゲームオブジェクトの描画
            player.draw(screen)

            for formation in enemy_formations:
                formation.draw(screen)

            if boss:
                boss.draw(screen)

            # スコア表示
            score_text = game_font.render(f"Enemies Defeated: {enemy_count}", True, WHITE)
            screen.blit(score_text, (10, 10))

            # 操作説明
            if not boss_spawned:
                help_text = game_font.render("Arrow Keys: Move, Space: Shoot, Shift: Toggle Invincible, ESC: Back to Title", True, WHITE)
                screen.blit(help_text, (10, SCREEN_HEIGHT - 30))

            # 無敵状態の表示
            if player.is_invincible():
                invincible_text = game_font.render("INVINCIBLE MODE", True, YELLOW)
                screen.blit(invincible_text, (10, 50))

        elif game_state == "game_over":
            # ゲームオーバー画面
            game_over_text = title_font.render("Game Over", True, RED)
            text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            screen.blit(game_over_text, text_rect)

            restart_text = button_font.render("Press R to Restart or ESC to Title", True, WHITE)
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 80))
            screen.blit(restart_text, restart_rect)

        elif game_state == "game_clear":
            # ゲームクリア画面（新しい豪華な画面を表示）
            clear_result = show_game_clear_screen()
            if clear_result == "restart":
                return run_game()
            elif clear_result == "title":
                return

        # 画面を更新
        pygame.display.flip()
        clock.tick(60)

def main():
    """メイン関数"""
    while True:
        result = show_title_screen()

        if result == "start":
            run_game()
        elif result == "end":
            pygame.quit()
            sys.exit()

if __name__ == "__main__":
    main()
