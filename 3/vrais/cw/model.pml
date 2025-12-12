#define DIR_ED 0
#define DIR_ES 1
#define DIR_SD 2
#define DIR_NS 3
#define DIR_DE 4
#define DIR_NE 5
#define DIR_COUNT 6

#define INTERSECTION_COUNT 6

bool sensor[DIR_COUNT];
bool request[DIR_COUNT];
bool traffic_light[DIR_COUNT];
bool intersection[INTERSECTION_COUNT];

mtype = {acquire, release};
chan resource_request = [0] of {byte /*dir*/, mtype};
chan wait_unlock[DIR_COUNT] = [0] of {bool /*unused*/};

inline set_intersections(dir, value) {
    atomic {
        if
        :: (dir == DIR_ED) ->
            intersection[0] = value;
            intersection[1] = value;
        :: (dir == DIR_ES) ->
            intersection[2] = value;
            intersection[5] = value;
        :: (dir == DIR_SD) ->
            intersection[5] = value;
            intersection[3] = value;
        :: (dir == DIR_NS) ->
            intersection[1] = value;
            intersection[3] = value;
            intersection[4] = value;
        :: (dir == DIR_DE) ->
            intersection[4] = value;
            intersection[5] = value;
        :: (dir == DIR_NE) ->
            intersection[0] = value;
            intersection[2] = value;
        :: else -> assert(false);
        fi
    }
}

// Процесс, моделирующий внешнюю среду
proctype environment() {
    do
    ::
        if
        :: (!sensor[0] && !traffic_light[0]) -> sensor[0] = true;
        :: (traffic_light[0] && sensor[0]) -> sensor[0] = false;
        :: (!sensor[1] && !traffic_light[1]) -> sensor[1] = true;
        :: (traffic_light[1] && sensor[1]) -> sensor[1] = false;
        :: (!sensor[2] && !traffic_light[2]) -> sensor[2] = true;
        :: (traffic_light[2] && sensor[2]) -> sensor[2] = false;
        :: (!sensor[3] && !traffic_light[3]) -> sensor[3] = true;
        :: (traffic_light[3] && sensor[3]) -> sensor[3] = false;
        :: (!sensor[4] && !traffic_light[4]) -> sensor[4] = true;
        :: (traffic_light[4] && sensor[4]) -> sensor[4] = false;
        :: (!sensor[5] && !traffic_light[5]) -> sensor[5] = true;
        :: (traffic_light[5] && sensor[5]) -> sensor[5] = false;
        fi
    od
}

proctype resource_manager() {
    byte dir;
    mtype type;
    do
    :: resource_request ? dir, type;
        if
        :: (type == acquire) ->
            request[dir] = true;
        :: (type == release) ->
            set_intersections(dir, false);
            wait_unlock[dir] ! false;
        :: else -> assert(false);
        fi

        atomic {
            if
            :: (request[DIR_ED] && !intersection[0] && !intersection[1]) ->
                intersection[0] = true;
                intersection[1] = true;
                request[DIR_ED] = false;
                wait_unlock[DIR_ED] ! false;
            :: (request[DIR_ES] && !intersection[2] && !intersection[5]) ->
                intersection[2] = true;
                intersection[5] = true;
                request[DIR_ES] = false;
                wait_unlock[DIR_ES] ! false;
            :: (request[DIR_SD] && !intersection[5] && !intersection[3]) ->
                intersection[5] = true;
                intersection[3] = true;
                request[DIR_SD] = false;
                wait_unlock[DIR_SD] ! false;
            :: (request[DIR_NS] && !intersection[1] && !intersection[3] && !intersection[4]) ->
                intersection[1] = true;
                intersection[3] = true;
                intersection[4] = true;
                request[DIR_NS] = false;
                wait_unlock[DIR_NS] ! false;
            :: (request[DIR_DE] && !intersection[4] && !intersection[5]) ->
                intersection[4] = true;
                intersection[5] = true;
                request[DIR_DE] = false;
                wait_unlock[DIR_DE] ! false;
            :: (request[DIR_NE] && !intersection[0] && !intersection[2]) ->
                intersection[0] = true;
                intersection[2] = true;
                request[DIR_NE] = false;
                wait_unlock[DIR_NE] ! false;
            :: else -> skip;
            fi
        }
    od
}

proctype traffic_light_controller(byte dir) {
    do
    ::
        if
        :: (sensor[dir] && !traffic_light[dir]) ->
            resource_request ! dir, acquire;
            wait_unlock[dir] ? _;
            traffic_light[dir] = true;
        :: (!sensor[dir] && traffic_light[dir]) ->
            traffic_light[dir] = false;
            resource_request ! dir, release;
            wait_unlock[dir] ? _;
        fi
    od
}

init {
    atomic {
        int i;
        i = 0;
        do
        :: i < DIR_COUNT ->
            sensor[i] = false;
            request[i] = false;
            traffic_light[i] = false;
            i++;
        :: else -> break
        od;

        i = 0;
        do
        :: i < INTERSECTION_COUNT ->
            intersection[i] = false;
            i++;
        :: else -> break
        od;

        run environment();
        run resource_manager();

        run traffic_light_controller(DIR_ED);
        run traffic_light_controller(DIR_NE);
        run traffic_light_controller(DIR_ES);
        run traffic_light_controller(DIR_SD);
        run traffic_light_controller(DIR_NS);
        run traffic_light_controller(DIR_DE);
    }
}

ltl test1 {[] !(traffic_light[DIR_ED] && traffic_light[DIR_NE])}
ltl test2 {[] !(traffic_light[DIR_ED] && traffic_light[DIR_NS])}
ltl test3 {[] !(traffic_light[DIR_ES] && traffic_light[DIR_NE])}
ltl test4 {[] !(traffic_light[DIR_ES] && traffic_light[DIR_SD])}
ltl test5 {[] !(traffic_light[DIR_ES] && traffic_light[DIR_DE])}
ltl test6 {[] !(traffic_light[DIR_NS] && traffic_light[DIR_SD])}
ltl test7 {[] !(traffic_light[DIR_NS] && traffic_light[DIR_DE])}
ltl test8 {[] !(traffic_light[DIR_SD] && traffic_light[DIR_DE])}

ltl test9 {[] ((sensor[DIR_ED] && !traffic_light[DIR_ED]) -> <> (traffic_light[DIR_ED]))}
ltl test10 {[] ((sensor[DIR_ES] && !traffic_light[DIR_ES]) -> <> (traffic_light[DIR_ES]))}
ltl test11 {[] ((sensor[DIR_SD] && !traffic_light[DIR_SD]) -> <> (traffic_light[DIR_SD]))}
ltl test12 {[] ((sensor[DIR_NS] && !traffic_light[DIR_NS]) -> <> (traffic_light[DIR_NS]))}
ltl test13 {[] ((sensor[DIR_DE] && !traffic_light[DIR_DE]) -> <> (traffic_light[DIR_DE]))}
ltl test14 {[] ((sensor[DIR_NE] && !traffic_light[DIR_NE]) -> <> (traffic_light[DIR_NE]))}
