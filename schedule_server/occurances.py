#
# private fun isOccurrence(date: LocalDate, start: LocalDate, recurrence: Period?): Boolean =
#     date.isEqual(
#         if (recurrence == null) start
#         else this.getClosestFutureOccurrence(date, start, recurrence)
#     )
#
# private fun getClosestFutureOccurrence(
#     date: LocalDate,
#     start: LocalDate,
#     recurrence: Period
# ): LocalDate {
#     var shiftedStart = start
#     if (recurrence.weeks != 0) {
#         val dateDOW = date.dayOfWeek
#         val startDOW = shiftedStart.dayOfWeek
#         // set startFrom's dow to be equal to date's dow, to add recurrence period correctly
#         if (startDOW < dateDOW) {
#             shiftedStart = shiftedStart.plusDays(dateDOW - startDOW)
#         } else if (startDOW > dateDOW) {
#             shiftedStart = shiftedStart.minusDays(startDOW - dateDOW)
#         }
#     }
#
#     var occurrence = shiftedStart
#
#     val distance = Days.daysBetween(shiftedStart, date).days
#     if (distance > 0) {
#         val factor = distance / Days.standardDaysIn(recurrence).days
#         if (factor > 0) {
#             val quickAdvance = recurrence.multipliedBy(factor)
#             occurrence = shiftedStart.plus(quickAdvance)
#         }
#     }
#
#     while (occurrence.isBefore(date)) {
#         occurrence = occurrence.plus(recurrence)
#     }
#
#     return occurrence
# }
import datetime
from datetime import timedelta


def get_closest_future_occurrence(date: datetime.date, start: datetime.date, recurrence: timedelta):
    occurrence = start
    if recurrence.days / 7 >= 1:
        date_dow = date.weekday()
        start_dow = start.weekday()
        if start_dow < date_dow:
            occurrence += timedelta(date_dow - start_dow)
        elif start_dow > date_dow:
            occurrence -= timedelta(start_dow - date_dow)

    distance = abs((occurrence - date).days)
    if distance > 0:
        factor = int(distance / recurrence.days)
        if factor > 0:
            quick_advance = recurrence * factor
            occurrence += quick_advance

    while occurrence < date:
        occurrence += recurrence

    return occurrence


def is_occurrence(date: datetime.date, start: datetime.date, recurrence: timedelta):
    return date == (start if not recurrence else get_closest_future_occurrence(date, start, recurrence))
