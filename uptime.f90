program uptime  ! prints current time, time computer has been on
  implicit none  ! and when computer was turned on
  integer, parameter :: dp = selected_real_kind(8)
  integer, parameter :: ip = selected_int_kind(16)
  integer, parameter :: iq = selected_int_kind(8)
  integer(ip)        :: hc_rate, hc_max, hc_t0
  integer(iq)        :: sc_rate, sc_max, sc_t0
  logical            :: prnt, clse, shrt, help
  real(dp)           :: h_rol, h_run, h_rate
  real(dp)           :: s_rol, s_run, s_rate
  real(dp)           :: diff, drif, mx_dif
  integer(ip)        :: hc_t1, c_time
  character(255)     :: arg, version
  integer(iq)        :: a, m

  call system_clock(hc_t0, hc_rate, hc_max)
  call system_clock(sc_t0, sc_rate, sc_max)
  c_time = time8(); version = '1.0'

  prnt = .false.; clse = .true.
  shrt = .false.; help = .false.
  m = command_argument_count(); a = 0
  do  ! parse arguments
    call get_command_argument(a, arg)
    if (len_trim(arg) == 0) exit
    select case(arg)
      case('-v', '-l') ! be verbose
        prnt = .true.  ! print additional time related info
    case('-vc', '-lc', '-cv', '-cl')
      prnt = .true.  ! be verbose and auto close
    clse = .false.
      case('-c')
        clse = .false. ! auto close program after printing info
      case('-s')       ! short form, print out just elapsed time
        shrt = .true.  ! and close (overrides all other arguments)
      case('-h', '-H', '--help', '--Help', '-help', '-Help', '-argh')
        help = .true.  ! print help and close (overrides all other arguments)
      case default
        continue
    end select
    a = a + 1
  end do

  if (help) then  ! print help
    print '(a)', 'Fortran based up time clock, version ' // trim(adjustl(version))
    print '(a)', 'prints out current time, last restart and elapsed time'
    print '(a)', 'ignores any time computer spent in hibernation or sleep mode'
    print '(a)', ''
    print '(a)', 'accepts the following arguments:'
    print '(a)', ' -v, -l'
    print '(a)', '   verbose, long form; prints out additional time related information'
    print '(a)', ''
    print '(a)', ' -c'
    print '(a)', '   close; auto closes program after running, no need to hit Enter/Return'
    print '(a)', ''
    print '(a)', ' -s'
    print '(a)', '   short form; print out just elapsed time in a readable form and quit'
    print '(a)', ''
    print '(a)', ' -h'
    print '(a)', '   help; show this information and quit'
    print '(a)', ''
    stop
  end if

  h_rate = real(hc_rate, dp)
  h_run  = real(hc_t0,   dp) / h_rate
  h_rol  = real(hc_max - hc_t0, dp) / h_rate

  s_rate = real(sc_rate, dp)
  s_run  = real(sc_t0,   dp) / s_rate
  s_rol  = real(sc_max - sc_t0, dp) / s_rate

  diff   = abs(s_run - h_run)
  drif   = diff / s_run  ! (difference / standard clock)
  mx_dif = real(sc_max, dp) / sc_rate
  ! mx_dif is the maximum difference between standard
  ! and high resolution clocks before switching which
  ! clock to show on short or standard forms; implies
  ! that the standard rolled over and is not correct.

  if (shrt) then            ! short form
    if (diff < mx_dif) then
      print '(a)', timecode(s_run)
    else
      print '(a)', timecode(h_run)
    end if
    stop
  else if (.not.prnt) then  ! standard form
    print '(a)', 'Current time : ' // ctime(c_time)
    if (diff < mx_dif) then
      print '(a)', 'Last Restart : ' // ctime(c_time - int(s_run, ip))
      print '(a)', 'Elapsed time : ' // timecode(s_run)
    else
      print '(a)', 'Last Restart : ' // ctime(c_time - int(h_run, ip))
      print '(a)', 'Elapsed time : ' // timecode(h_run)
    end if
  else                      ! verbose, long form
    print '(a)', 'Current time : ' // ctime(c_time)
    print '(a)', ''
    print '(a)', 'Standard resolution clock:'
    print '(a)', '  Last Restart : ' // ctime(c_time - int(s_run, ip))
    print '(a)', '  Elapsed time : ' // timecode(s_run)
    print '(a)', ''
    print '(a)', '  Clock   rate : ' // comma(int(sc_rate, ip)) // ' counts/sec'
    print '(a)', '  Rollover  in : ' // timecode(s_rol)
  print '(a)', '  Rollover  at : ' // ctime(c_time + int(s_rol, ip))
    print '(a)', ''
    print '(a)', 'High resolution clock:'
    print '(a)', '  Last Restart : ' // ctime(c_time - int(h_run, ip))
    print '(a)', '  Elapsed time : ' // timecode(h_run)
    print '(a)', ''
    print '(a)', '  Clock   rate : ' // comma(hc_rate) // ' counts/sec'
    print '(a)', '  Rollover  in : ' // timecode(h_rol)
    print '(a)', ''
    print '(a)', '  Difference   : ' // timecode(diff, '(f08.05)')
    print '("  Drift (s/s)  : ",es10.4)', drif
    !print '(a)', '  Max diff.    : ' // timecode(mx_dif, '(f10.07)')
    print '(a)', ''
    call system_clock(hc_t1)
    print '(a)', 'Process time : ' // timecode(real(hc_t1 - hc_t0, dp) / h_rate, '(f09.07)')
  end if

  if (clse) then  ! wait for key press
    print '(a)', ''
    print '(a)', 'Press Enter/Return to close...'
    read(*, *)
  else            ! auto close
    continue
  end if

  contains
    function timecode(secs, ft) result (res)  ! 12345 -> '3h 25m 45s'
      ! optional argument ft must be 8 characters long {ex: '(f09.06)'}
      ! ft is a format for seconds (how many digits after decimal point)
      integer, parameter :: dp = selected_real_kind(8)
      integer, parameter :: ip = selected_int_kind(16)
      integer(ip), parameter :: y = 31556952, m = 60
      integer(ip), parameter :: d = 86400, h = 3600
      integer(ip) :: yr, dy, hr, mn; real(dp) :: sc
      character(255) :: str, ys, ds, hs, ms, ss
      character(:), allocatable :: res
      character(8), optional :: ft
      real(dp), intent(in) :: secs
      character(8) :: frmt
      real(dp) :: chk
      frmt = '(f04.00)'  ! '(f09.06)'
      if (present(ft)) frmt = ft
      sc = abs(secs)
      yr = int(sc / real(y, dp), ip); sc = sc - real((yr * y), dp)
      dy = int(sc / real(d, dp), ip); sc = sc - real((dy * d), dp)
      hr = int(sc / real(h, dp), ip); sc = sc - real((hr * h), dp)
      mn = int(sc / real(m, dp), ip); sc = sc - real((mn * m), dp)

      if (frmt(7:7) == '0') then  ! no fractional seconds
        write(ss, '(i02)') int(sc, ip)
      else
        write(ss, frmt) sc
      end if

      str = trim(adjustl(ss)) // 's'
      read(ss, *) chk  ! if seconds are 0, leave blank
      if (chk == 0) str = ''

      if (mn > 0) then  ! add in as needed
        write(ms, '(i02,"m")') mn
        str = trim(adjustl(ms)) // ' ' // str
      end if
      if (hr > 0) then
        write(hs, '(i02,"h")') hr
        str = trim(adjustl(hs)) // ' ' // str
      end if
      if (dy > 0) then
        write(ds, '(i03,"d")') dy
        str = trim(adjustl(ds)) // ' ' // str
      end if
      if (yr > 0) then
        write(ys, '(i50"y")') yr
        str = trim(adjustl(ys)) // ' ' // str
      end if
      res = trim(adjustl(str))
    end function timecode

    recursive function comma(v) result(res)   ! 1234567890 -> '1,234,567,890'
      character(:), allocatable :: res
      character(90) :: tmp1, tmp2
      integer(ip) :: v, c, b
      c = abs(v); b = 1000
      if (c >= b) then  ! internal part of number, have zeros
        write(tmp1, '(i3.3)') mod(c, b)
        tmp2 = trim(adjustl(comma(c / b))) // ',' // trim(adjustl(tmp1))
      else  ! front of number, have no leading zeros
        write(tmp1, '(i03)') mod(c, b)
        tmp2 = trim(adjustl(tmp1))
      end if
      if (v < 0) then
        res = trim(adjustl('-' // tmp2))
      else
        res = trim(adjustl(tmp2))
      end if
    end function comma
end program uptime
