/*
35, 39, 11, 2
SD - DE, ES - DE, NE - ED, NS - SD
*/

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
    int dir;
    do
    :: 
        atomic {
            dir = 0;
            do
            :: dir < DIR_COUNT ->
                if
                :: (!sensor[dir]) -> sensor[dir] = true;
                :: (traffic_light[dir] && sensor[dir]) -> sensor[dir] = false;
                :: skip;
                fi;
                dir++;
            :: else -> break
            od
        }
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
            request[dir] = false;
            set_intersections(dir, false);
        :: else -> assert(false);
        fi

        atomic {
            if
            :: (request[DIR_ED] && !intersection[0] && !intersection[1]) ->
                intersection[0] = true;
                intersection[1] = true;
                wait_unlock[DIR_ED] ! false;
            :: (request[DIR_ES] && !intersection[2] && !intersection[5]) ->
                intersection[2] = true;
                intersection[3] = true;
                wait_unlock[DIR_ES] ! false;
            :: (request[DIR_SD] && !intersection[5] && !intersection[3]) ->
                intersection[5] = true;
                intersection[3] = true;
                wait_unlock[DIR_SD] ! false;
            :: (request[DIR_NS] && !intersection[1] && !intersection[3] && !intersection[4]) ->
                intersection[1] = true;
                intersection[3] = true;
                intersection[4] = true;
                wait_unlock[DIR_NS] ! false;
            :: (request[DIR_DE] && !intersection[4] && !intersection[5]) ->
                intersection[4] = true;
                intersection[5] = true;
                wait_unlock[DIR_DE] ! false;
            :: (request[DIR_NE] && !intersection[0] && !intersection[2]) ->
                intersection[0] = true;
                intersection[2] = true;
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
        :: (!sensor[dir] && request[dir]) ->
            traffic_light[dir] = false;
            resource_request ! dir, release;
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
    }
}

ltl test {[] !(traffic_light[DIR_ED] && traffic_light[DIR_NE])}
